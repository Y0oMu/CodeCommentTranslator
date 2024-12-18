import os
import re
from typing import List, Dict
from abc import ABC, abstractmethod

class CommentExtractor(ABC):
    """Base class for language-specific comment extractors"""

    @abstractmethod
    def extract_comments(self, content: str) -> Dict[int, Dict[str, str]]:
        """
        Extract comments from file content
        Returns: Dict[line_number, Dict[
            'content': str,  # The comment content
            'start': int,    # Start position in line
            'end': int,      # End position in line
            'original': str, # Original comment with markers
            'type': str,     # Comment type (inline/multiline/docstring)
            'extra': dict    # Extra information specific to language
        ]]
        """
        pass

    @abstractmethod
    def replace_comments(self, content: str, translations: Dict[int, str]) -> str:
        """
        Replace comments in content with translations
        Args:
            content: Original file content
            translations: Dict[line_number, translated_text]
        Returns:
            Modified content with replaced comments
        """
        pass
class CStyleCommentExtractor(CommentExtractor):
    """Extracts comments from C++ files"""

    def extract_comments(self, content: str) -> Dict[int, Dict[str, str]]:
        comments = {}

        # Track positions of multiline comments
        multiline_positions = set()

        # C-style multiline comments
        for match in re.finditer(r'/\*[\s\S]*?\*/', content):
            start_pos = match.start()
            end_pos = match.end()

            # Skip if this is part of a string literal
            if self._is_in_string(content, start_pos):
                continue

            line_num = content[:start_pos].count('\n') + 1
            original = match.group()

            # Add all positions covered by this comment
            for i in range(start_pos, end_pos):
                multiline_positions.add(i)

            comments[line_num] = {
                'content': self._extract_multiline_content(original),
                'start': len(content[:start_pos].split('\n')[-1]),
                'end': end_pos,
                'original': original,
                'type': 'multiline',
                'extra': {
                    'positions': (start_pos, end_pos),
                    'line_count': original.count('\n') + 1
                }
            }

        # C-style single-line comments
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            # Skip preprocessor directives
            if line.strip().startswith('#'):
                continue

            # Find all // comments in the line
            for match in re.finditer(r'//', line):
                pos = match.start()
                pos_in_file = sum(len(l) + 1 for l in lines[:i-1]) + pos

                # Skip if this position is already part of a multiline comment
                # or if it's inside a string
                if pos_in_file in multiline_positions or self._is_in_string(line[:pos], pos):
                    continue

                comment_text = line[pos:]
                comments[i] = {
                    'content': comment_text[2:].strip(),
                    'start': pos,
                    'end': len(line),
                    'original': comment_text,
                    'type': 'inline',
                    'extra': {
                        'has_code': bool(line[:pos].strip())
                    }
                }

        return comments

    def replace_comments(self, content: str, translations: Dict[int, str]) -> str:
        lines = content.split('\n')

        # Process each translation
        for line_num, translation in sorted(translations.items(), reverse=True):
            comment_info = self.extract_comments(content)[line_num]

            if comment_info['type'] == 'inline':
                original_line = lines[line_num - 1]
                has_code = comment_info['extra']['has_code']

                if has_code:
                    # Preserve code part and replace only the comment
                    code_part = original_line[:comment_info['start']]
                    lines[line_num - 1] = f"{code_part}// {translation.strip()}"
                else:
                    # Full line comment
                    indentation = ' ' * comment_info['start']
                    lines[line_num - 1] = f"{indentation}// {translation.strip()}"
            else:
                # Replace multiline comment
                indentation = ' ' * comment_info['start']
                formatted_lines = [f"{indentation}/*"]
                for line in translation.split('\n'):
                    formatted_lines.append(f"{indentation} * {line.strip()}")
                formatted_lines.append(f"{indentation} */")

                # Calculate the range of lines to replace
                line_count = comment_info['extra']['line_count']
                lines[line_num-1:line_num-1+line_count] = formatted_lines

        return '\n'.join(lines)

    def _extract_multiline_content(self, comment: str) -> str:
        # Remove /* and */ and any * at the start of lines
        content = re.sub(r'/\*[\s\*]*|\*/\s*$', '', comment)
        content = re.sub(r'^\s*\*\s?', '', content, flags=re.MULTILINE)
        return content.strip()

    def _is_in_string(self, content: str, pos: int) -> bool:
        """Check if a position is inside a string literal"""
        # Count unescaped quotes before the position
        content = content[:pos]

        # Handle string literals
        in_single_quote = False
        in_double_quote = False
        i = 0
        while i < len(content):
            if content[i] == '\\':
                i += 2  # Skip escaped character
                continue
            elif content[i] == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif content[i] == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            i += 1

        return in_single_quote or in_double_quote

class PythonCommentExtractor(CommentExtractor):
    """Extracts comments from Python files"""

    def extract_comments(self, content: str) -> Dict[int, Dict[str, str]]:
        comments = {}
        lines = content.split('\n')

        # Track positions of docstrings
        docstring_positions = set()

        # Modify the docstring pattern to better handle nested and multi-line cases
        docstring_pattern = r'(\'\'\'[\s\S]*?\'\'\'|"""[\s\S]*?""")'

        current_pos = 0
        while True:
            match = re.search(docstring_pattern, content[current_pos:])
            if not match:
                break

            start_pos = current_pos + match.start()
            end_pos = current_pos + match.end()

            # Ensure this position is not within other strings
            if not self._is_in_string(content[:start_pos], start_pos):
                # Calculate line number
                line_num = content[:start_pos].count('\n') + 1
                original = match.group().strip()

                # Analyze the context to determine if it is a true docstring
                prev_lines = content[:start_pos].split('\n')
                if prev_lines:
                    last_line = prev_lines[-1].strip()
                    # Check if it is a docstring after class definition, function definition, or an assignment statement
                    if (last_line.endswith(':') or 
                        last_line.endswith('=') or 
                        line_num == 1 or 
                        # Module-level docstring

                        re.match(r'^[ \t]*["\']', match.group())):  # docstring at the beginning of the line
                        # Testing
                        comments[line_num] = {
                            'content': original[3:-3].strip(),
                            'start': len(prev_lines[-1]) - len(prev_lines[-1].lstrip()),
                            'end': end_pos - current_pos,
                            'original': original,
                            'type': 'docstring',
                            'extra': {
                                'quote_type': original[:3],
                                'line_count': original.count('\n') + 1
                            }
                        }
                        # Records all positions covered by this docstring
                        for i in range(start_pos, end_pos):
                            docstring_positions.add(i)

            current_pos = end_pos

        # Python single-line comment handling remains unchanged
        for i, line in enumerate(lines, 1):
            if '#' in line:
                pos = line.find('#')
                pos_in_file = sum(len(l) + 1 for l in lines[:i-1]) + pos

                # Skip if this position is inside a docstring or string
                if pos_in_file in docstring_positions or self._is_in_string(line[:pos], pos):
                    continue

                # Skip shebang and encoding declarations
                if i == 1 and line.strip().startswith('#!'):
                    continue
                if i <= 2 and 'coding' in line:
                    continue

                comment_text = line[pos:]
                comments[i] = {
                    'content': comment_text[1:].strip(),
                    'start': pos,
                    'end': len(line),
                    'original': comment_text,
                    'type': 'inline',
                    'extra': {
                        'has_code': bool(line[:pos].strip())
                    }
                }

        return comments

    def replace_comments(self, content: str, translations: Dict[int, str]) -> str:
        lines = content.split('\n')

        # Process each translation
        for line_num, translation in sorted(translations.items(), reverse=True):
            comment_info = self.extract_comments(content)[line_num]

            if comment_info['type'] == 'inline':
                original_line = lines[line_num - 1]
                has_code = comment_info['extra']['has_code']

                if has_code:
                    # Preserve code part and replace only the comment
                    code_part = original_line[:comment_info['start']]
                    lines[line_num - 1] = f"{code_part}# {translation.strip()}"
                else:
                    # Full line comment
                    indentation = ' ' * comment_info['start']
                    lines[line_num - 1] = f"{indentation}# {translation.strip()}"
            else:
                # Replace docstring
                quote_type = comment_info['extra']['quote_type']
                indentation = ' ' * comment_info['start']
                formatted_lines = [
                    f"{indentation}{quote_type}",
                    *[f"{indentation}{line.strip()}" for line in translation.split('\n')],
                    f"{indentation}{quote_type}"
                ]

                # Replace the lines
                line_count = comment_info['extra']['line_count']
                lines[line_num-1:line_num-1+line_count] = formatted_lines

        return '\n'.join(lines)

    def _is_in_string(self, content: str, pos: int) -> bool:
        """Check if a position is inside a string literal"""
        # Handle string literals
        in_single_quote = False
        in_double_quote = False
        i = 0
        while i < len(content):
            if content[i] == '\\':
                i += 2  # Skip escaped character
                continue
            elif content[i] == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif content[i] == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            i += 1

        return in_single_quote or in_double_quote
    
class FileDetector:
    """Detects and processes code files"""

    SUPPORTED_EXTENSIONS = {'.py', '.cpp','c','.js'}
    EXTRACTORS = {
        '.c': CStyleCommentExtractor(),
        '.cpp': CStyleCommentExtractor(),
        '.py': PythonCommentExtractor(),
        '.js': CStyleCommentExtractor()
    }

    @classmethod
    def detect_code_files(cls, target_path: str) -> List[str]:
        """Detect all code files in the given path"""
        target_path = os.path.abspath(target_path)

        if os.path.isfile(target_path):
            return [target_path] if cls._is_code_file(target_path) else []

        code_files = []
        for root, _, files in os.walk(target_path):
            for file in files:
                full_path = os.path.join(root, file)
                if cls._is_code_file(full_path):
                    code_files.append(full_path)

        return code_files

    @classmethod
    def _is_code_file(cls, file_path: str) -> bool:
        """Check if the file is a supported code file"""
        return os.path.splitext(file_path)[1] in cls.SUPPORTED_EXTENSIONS

    @classmethod
    def extract_comments(cls, file_path: str) -> Dict[int, Dict[str, str]]:
        """Extract comments from a given code file"""
        file_extension = os.path.splitext(file_path)[1]

        if file_extension not in cls.EXTRACTORS:
            return {}

        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        return cls.EXTRACTORS[file_extension].extract_comments(content)

    @classmethod
    def replace_comments(cls, file_path: str, translations: Dict[int, str]) -> bool:
        """Replace comments in file with translations"""
        file_extension = os.path.splitext(file_path)[1]

        if file_extension not in cls.EXTRACTORS:
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            extractor = cls.EXTRACTORS[file_extension]
            new_content = extractor.replace_comments(content, translations)

            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(new_content)

            return True
        except Exception as e:
            print(f"Error replacing comments in {file_path}: {e}")
            return False