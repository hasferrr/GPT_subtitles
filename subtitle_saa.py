import re
from translate_gpt import Subtitle
from typing import List

class SubtitleSAA(Subtitle):
    """
    Extends `Subtitle` class

    Used for SubStation Alpha (SSA) file or `.ass` file format

    Make sure you have remove kara dialogue manually from the subtitle
    """
    def __init__(self, file_path: str):
        super().__init__(file_path)

        if ('[Events]' not in self.content or 'Dialogue: ' not in self.content):
            raise Exception('Invalid SAA')

        self.content_list = self.content.split('\n')
        self.content_dialogue: List[str] = []

        # Split only for dialogue (Events)
        # not including Script Info, V4+ Styles, etc
        for i, line in enumerate(self.content_list):
            if line == '[Events]':
                self.content_dialogue = self.content_list[i+2:-1]
                break

    def getLinesBeforeDialogue(self):
        for i, line in enumerate(self.content_list):
            if line == '[Events]':
                return '\n'.join(self.content_list[:i+2])
        return ''

    # @override
    def save_subtitles(self, file_path: str, content: str):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.getLinesBeforeDialogue())
            f.write(content)

    # @override
    def split_subtitles(self, _):
        raise Exception('call get_processed_batches_and_timestamps')

    # @override
    def process_subtitles(self, _):
        raise Exception('call get_processed_batches_and_timestamps')

    # @override
    def get_processed_batches_and_timestamps(self, batch_size: int):
        batches: List[str] = []
        timestamps: List[List[str]] = []

        batch_count = 1
        dialogue_number = 1
        combined_dialogue: List[str] = []
        times: List[str] = []

        cm = self.content_dialogue[0].count(',')

        for dialogue in self.content_dialogue:
            if (dialogue.startswith('Comment:')):
                continue

            # split on the cm'th index
            split_idx = -1
            for _ in range(cm):
                split_idx = dialogue.find(',', split_idx + 1)
                if split_idx == -1:
                    break
            split_idx += 1

            # generate partial batch
            combined_dialogue.append(f'{dialogue_number}\n{dialogue[split_idx:]}')
            times.append(dialogue[:split_idx])

            # combine into single batch
            if batch_count == batch_size:
                batches.append('\n\n'.join(combined_dialogue))
                timestamps.append(times)
                batch_count = 0
                combined_dialogue = []
                times = []

            batch_count += 1
            dialogue_number += 1

        if combined_dialogue:
            batches.append('\n\n'.join(combined_dialogue))
            timestamps.append(times)

        return batches, timestamps

    @staticmethod
    def merge_subtitles_with_timestamps(translated_subtitles: str, timestamps: List[str]):
        translated_lines = translated_subtitles.split('\n')
        merged_lines: List[str] = []

        timestamp_idx = 0
        for line in translated_lines:
            if not re.match(r'\d+\s*$', line) and line != '':
                merged_lines.append(timestamps[timestamp_idx] + line)
                timestamp_idx += 1

        return '\n'.join(merged_lines)
