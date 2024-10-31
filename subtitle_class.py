import re
from typing import List

class Subtitle:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.content = self.load_subtitles()

    def load_subtitles(self):
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def save_subtitles(self, file_path: str, content: str):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def split_subtitles(self, batch_size: int):
        subtitle_blocks = self.content.strip().split('\n\n')
        batches: List[str] = []

        for i in range(0, len(subtitle_blocks), batch_size):
            batch = '\n\n'.join(subtitle_blocks[i:i + batch_size])
            batches.append(batch)

        return batches

    def process_subtitles(self, subtitles: str):
        lines = subtitles.split('\n')
        processed_lines: List[str] = []
        timestamps: List[str] = []

        for line in lines:
            if re.match(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}', line):
                timestamps.append(line)
            else:
                processed_lines.append(line)

        return '\n'.join(processed_lines), timestamps

    def get_processed_batches_and_timestamps(self, batch_size: int):
        """
        Example (batch_size=2):
        processed_batches = ['1\nMs. Kano!\n\n2\nDid she go already?']
        timestamps_batches = [['00:00:04,800 --> 00:00:06,170', '00:00:06,260 --> 00:00:08,260']]
        """
        subtitle_batches = self.split_subtitles(batch_size)
        processed_batches: List[str] = []
        timestamps_batches: List[List[str]] = []
        for batch in subtitle_batches:
            processed_batch, timestamps = self.process_subtitles(batch)
            processed_batches.append(processed_batch.replace('\ufeff', ''))
            timestamps_batches.append(timestamps)
        return processed_batches, timestamps_batches

    @staticmethod
    def merge_subtitles_with_timestamps(translated_subtitles: str, timestamps: List[str]):
        translated_lines = translated_subtitles.split('\n')
        merged_lines: List[str] = []

        timestamp_idx = 0
        for line in translated_lines:
            if re.match(r'\d+\s*$', line):
                merged_lines.append(line)
                merged_lines.append(timestamps[timestamp_idx])
                timestamp_idx += 1
            else:
                merged_lines.append(line)

        return '\n'.join(merged_lines)


class SubtitleSSA(Subtitle):
    """
    Extends `Subtitle` class\n
    Used for SubStation Alpha (SSA) file or `.ass` file format\n
    Make sure you have remove kara dialogue manually from the subtitle
    """
    def __init__(self, file_path: str):
        super().__init__(file_path)

        if ('[Events]' not in self.content or 'Dialogue: ' not in self.content):
            raise Exception('Invalid SAA')

        self.content_list = self.content.split('\n')
        self.content_dialogue: List[str] = []
        self.last_dialogue_idx: int | None = None

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

    def getLinesAfterDialogue(self):
        if self.last_dialogue_idx != None:
            return '\n'.join(self.content_dialogue[self.last_dialogue_idx + 1:])
        return ''

    # @override
    def save_subtitles(self, file_path: str, content: str):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(self.getLinesBeforeDialogue())
            f.write(content)
            f.write('\n')
            f.write(self.getLinesAfterDialogue())

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

        for i, dialogue in enumerate(self.content_dialogue):
            if (not dialogue.startswith('Dialogue:')):
                continue

            self.last_dialogue_idx = i

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
