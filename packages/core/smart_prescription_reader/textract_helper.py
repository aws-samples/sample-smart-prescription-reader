# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import logging
from typing import TYPE_CHECKING

# adapted from https://github.com/aws-samples/textract-paragraph-identification/tree/main

if TYPE_CHECKING:
    from mypy_boto3_textract.type_defs import DetectDocumentTextResponseTypeDef

logger = logging.getLogger(__name__)


def get_headers_to_child_mapping(font_sizes_and_line_numbers):
    unique_font_heights = []
    for font_height in font_sizes_and_line_numbers:
        lines_with_same_font = font_sizes_and_line_numbers[font_height]
        if len(lines_with_same_font) > 1:
            unique_font_heights.append(font_height)

    fonts_for_headers = list(set(unique_font_heights))
    i = 0
    headers_and_its_child = {}
    while i + 1 < len(fonts_for_headers):
        headers_and_its_child[fonts_for_headers[i]] = fonts_for_headers[i + 1]
        i += 1
    return headers_and_its_child


def get_the_text_with_required_info(collection_of_textract_responses: list["DetectDocumentTextResponseTypeDef"]):
    total_text = []
    total_text_with_info = []
    running_sequence_number = 0

    font_sizes_and_line_numbers = {}
    for page in collection_of_textract_responses:
        per_page_text = []
        blocks = page["Blocks"]
        for block in blocks:
            if block["BlockType"] == "LINE":
                block_text_dict = {}
                running_sequence_number += 1
                block_text_dict.update(text=block["Text"])
                # block_text_dict.update(page=block['Page'])
                block_text_dict.update(
                    page=1
                )  # modified to only get text from single page documents - strunkjd@amazon.com
                block_text_dict.update(left_indent=round(block["Geometry"]["BoundingBox"]["Left"], 2))
                font_height = round(block["Geometry"]["BoundingBox"]["Height"], 3)
                line_number = running_sequence_number
                block_text_dict.update(font_height=round(block["Geometry"]["BoundingBox"]["Height"], 3))
                block_text_dict.update(indent_from_top=round(block["Geometry"]["BoundingBox"]["Top"], 2))
                block_text_dict.update(text_width=round(block["Geometry"]["BoundingBox"]["Width"], 2))
                block_text_dict.update(line_number=running_sequence_number)

                if font_height in font_sizes_and_line_numbers:
                    line_numbers = font_sizes_and_line_numbers[font_height]
                    line_numbers.append(line_number)
                    font_sizes_and_line_numbers[font_height] = line_numbers
                else:
                    line_numbers = []
                    line_numbers.append(line_number)
                    font_sizes_and_line_numbers[font_height] = line_numbers

                total_text.append(block["Text"])
                per_page_text.append(block["Text"])
                total_text_with_info.append(block_text_dict)

    return total_text_with_info, font_sizes_and_line_numbers


def get_text_with_line_spacing_info(total_text_with_info):
    i = 1
    text_info_with_line_spacing_info = []
    while i < len(total_text_with_info) - 1:
        previous_line_info = total_text_with_info[i - 1]
        current_line_info = total_text_with_info[i]
        next_line_info = total_text_with_info[i + 1]
        if (
            current_line_info["page"] == next_line_info["page"]
            and previous_line_info["page"] == current_line_info["page"]
        ):
            line_spacing_after = round(
                (next_line_info["indent_from_top"] - current_line_info["indent_from_top"]),
                2,
            )
            spacing_with_prev = round(
                (current_line_info["indent_from_top"] - previous_line_info["indent_from_top"]),
                2,
            )
            current_line_info.update(line_space_before=spacing_with_prev)
            current_line_info.update(line_space_after=line_spacing_after)
            text_info_with_line_spacing_info.append(current_line_info)
        else:
            text_info_with_line_spacing_info.append(None)
        i += 1
    return text_info_with_line_spacing_info


def extract_paragraphs_only(data):
    paras = []
    i = 0
    paragraph_data = []
    while i < len(data):
        logger.debug(i)
        line = data[i]
        if line:
            if line["line_space_before"] > line["line_space_after"]:
                paras.append("\n".join(paragraph_data))  # Added newline instead of empty string - strunkjd@amazon.com
                paragraph_data = [line["text"]]
                if i < len(data) - 1:
                    next_line = data[i + 1]
                    if next_line and line["text_width"] > next_line["text_width"] / 2:
                        paragraph_data.append(next_line["text"])
                        i += 1
                    else:
                        paras.append(" ".join(paragraph_data))
                        paragraph_data = []
            else:
                paragraph_data.append(line["text"])
        i += 1
    return paras


def get_paragraphs_based_on_period(data):
    paragraph_data = []
    paras = []
    i = 0
    while i < len(data):
        line = data[i]
        if line:
            if line["text"][-1] == ".":
                paragraph_data.append(line["text"])
                paras.append(" ".join(paragraph_data))
                paragraph_data = []
            else:
                paragraph_data.append(line["text"])
        i += 1
    return paras


def get_paragraphs(response: "DetectDocumentTextResponseTypeDef") -> str:
    (
        total_text_with_info,
        font_sizes_and_line_numbers,
    ) = get_the_text_with_required_info([response])
    text_with_line_spacing_info = get_text_with_line_spacing_info(total_text_with_info)
    paragraphs = extract_paragraphs_only(text_with_line_spacing_info)
    document = ""
    for p in paragraphs:
        document += p + "\n"

    return document
