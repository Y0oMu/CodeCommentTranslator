import argparse
import os
import sys
import yaml
from typing import List, Dict, Tuple
import re
from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import clear
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import concurrent.futures

from src.file_detector import FileDetector
from src.translator import create_translator
from src.language_detector import LanguageDetector

class CodeCommentTranslator:
    def __init__(self, target_path: str, config_path: str = "config.yaml", debug: bool = False):
        """
        Initialize the CodeCommentTranslator

        Args:
            target_path (str): Path to file or directory to process
            config_path (str): Path to configuration file
            debug (bool): Enable debug mode for detailed output
        """
        self.target_path = target_path
        self.config_path = config_path
        self.debug = debug
        self.detected_files: List[str] = []
        self.console = Console()
        self.session = PromptSession()

        # Load configuration
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            self.console.print(f"[red]Failed to load config file: {e}[/red]")
            sys.exit(1)

        # Initialize translator
        try:
            self.translator = create_translator(config_path)
        except Exception as e:
            self.console.print(f"[red]Failed to initialize translator: {e}[/red]")
            sys.exit(1)

        translation_config = self.config.get('translation', {})
        self.target_language = translation_config.get('target_language', 'en')
        self.source_language = translation_config.get('source_language', None)
        self.max_workers = translation_config.get('max_workers', 1)
        if self.source_language and self.source_language.lower() not in ['any', 'en', 'zh', 'jp']:
            self.console.print(f"[yellow]Warning: Unsupported source language '{self.source_language}'. Using 'any'.[/yellow]")
            self.source_language = None
        # Fixed page size for display
        self.page_size = 10

    def detect_files(self) -> None:
        """
        Detect code files in the target path and filter based on source language
        """
        all_files = FileDetector.detect_code_files(self.target_path)

        if not all_files:
            self.console.print(f"[red]No supported code files found in {self.target_path}[/red]")
            sys.exit(1)

        # If source language is specified, filter files that contain comments in that language
        if self.source_language and self.source_language.lower() not in ['any', None]:
            filtered_files = []
            for file_path in all_files:
                comments = FileDetector.extract_comments(file_path)
                if comments:
                    # Check if any comment in the file matches the source language
                    for info in comments.values():
                        if LanguageDetector.should_translate(info['content'], self.source_language):
                            filtered_files.append(file_path)
                            break

            if not filtered_files:
                self.console.print(f"[red]No files found with comments in {self.source_language} language[/red]")
                sys.exit(1)

            self.detected_files = filtered_files
        else:
            self.detected_files = all_files

        if self.debug:
            total_files = len(all_files)
            filtered_files = len(self.detected_files)
            if total_files != filtered_files:
                self.console.print(f"[yellow]Filtered {filtered_files} files with {self.source_language} comments from {total_files} total files[/yellow]")

    def display_files(self, start_index: int = 0) -> None:
        """
        Display detected files in batches
        """
        end_index = min(start_index + self.page_size, len(self.detected_files))

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim", width=4)
        table.add_column("File Path", style="cyan")
        if self.debug:
            table.add_column("Comment Languages", style="green")

        for i in range(start_index, end_index):
            file_path = self.detected_files[i]
            if self.debug:
                # 获取文件中的注释语言
                comments = FileDetector.extract_comments(file_path)
                languages = set()
                for info in comments.values():
                    lang = LanguageDetector.detect_language(info['content'])
                    if lang:
                        languages.add(lang)
                lang_str = ", ".join(sorted(languages)) if languages else "unknown"
                table.add_row(str(i), file_path, lang_str)
            else:
                table.add_row(str(i), file_path)

        title = f"Detected Code Files"
        if self.source_language and self.source_language.lower() not in ['any', None]:
            title += f" (Filtered for {self.source_language} comments)"

        self.console.print(Panel(table, title=title))

        if end_index < len(self.detected_files):
            self.console.print("[yellow]More files available. Press ↓ or type 'next' to see more.[/yellow]")

        self.console.print("\n[bold green]Commands:[/bold green]")
        self.console.print("- [cyan]show [id][/cyan]: Display comments in the file")
        self.console.print("- [cyan]y[/cyan]: Translate all files")
        self.console.print("- [cyan]next[/cyan]: Show more files")
        self.console.print("- [cyan]back[/cyan]: Return to file list (when showing comments)")
        self.console.print("- [cyan]quit[/cyan]: Exit program")

    def show_comments(self, file_index: int, start_index: int = 0) -> None:
        """
        Show comments for a specific file without translation
        """
        if 0 <= file_index < len(self.detected_files):
            file_path = self.detected_files[file_index]
            comments = FileDetector.extract_comments(file_path)

            if comments:
                self.console.print(f"\n[bold green]Comments in {file_path}:[/bold green]")

                # Get sorted line numbers
                line_nums = sorted(comments.keys())
                end_index = min(start_index + self.page_size, len(line_nums))

                # Display comments in current batch
                for i in range(start_index, end_index):
                    line_num = line_nums[i]
                    if self.debug:
                        self.console.print(f"\n[cyan]Line {line_num}:[/cyan]")
                        self.console.print(comments[line_num])
                    else:
                        self.console.print(f"[cyan]Line {line_num}:[/cyan] {comments[line_num]['content']}")

                if end_index < len(line_nums):
                    self.console.print("\n[yellow]More comments available. Type 'next' to see more.[/yellow]")
                self.console.print("\n[yellow]Use 'back' to return to file list[/yellow]")
            else:
                self.console.print(f"[yellow]No comments found in {file_path}[/yellow]")
        else:
            self.console.print("[red]Invalid file index[/red]")

    def translate_file(self, file_path: str) -> bool:
        """
        Translate comments in a single file with language detection
        """
        try:
            comments = FileDetector.extract_comments(file_path)
            if not comments:
                self.console.print(f"[yellow]No comments found in {file_path}[/yellow]")
                return True

            # Filter comments based on language detection
            comments_to_translate = {}
            for line, info in comments.items():
                if LanguageDetector.should_translate(info['content'], self.source_language):
                    comments_to_translate[line] = info['content']
                elif self.debug:
                    self.console.print(f"[yellow]Skipping line {line} - not in source language {self.source_language}[/yellow]")

            if not comments_to_translate:
                self.console.print(f"[yellow]No comments in source language found in {file_path}[/yellow]")
                return True

            # Translate filtered comments
            translated_comments = self.translator.translate_batch(
                comments_to_translate,
                self.target_language,
            )

            # Process translated comments
            processed_translations = {}
            for line_num, translation in translated_comments.items():
                original_comment = comments[line_num]

                # Handle inline comments with multiple lines in translation
                if original_comment['type'] == 'inline' and '\n' in translation:
                    first_line = translation.split('\n')[0].strip()
                    original_markers = ""
                    original_content = original_comment['original'].strip()

                    if original_content.startswith('//'):
                        original_markers = '//'
                    elif original_content.startswith('#'):
                        original_markers = '#'
                    elif original_content.startswith('/*'):
                        original_markers = '/*'

                    if original_markers:
                        processed_translations[line_num] = f"{original_markers} {first_line}"
                    else:
                        processed_translations[line_num] = first_line

                    if self.debug:
                        self.console.print(f"[yellow]Warning: Multi-line translation detected for inline comment at line {line_num}. Using first line only.[/yellow]")
                else:
                    processed_translations[line_num] = translation

            # Replace comments in file
            if FileDetector.replace_comments(file_path, processed_translations):
                self.console.print(f"[green]Successfully translated comments in {file_path}[/green]")
                return True
            return False

        except Exception as e:
            self.console.print(f"[red]Error translating {file_path}: {str(e)}[/red]")
            return False

    def translate_all_files(self) -> None:
        """
        Translate comments in all detected files with concurrent execution
        """
        total_files = len(self.detected_files)
        self.console.print(f"\n[bold]Starting translation of {total_files} files with {self.max_workers} workers[/bold]")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all translation tasks
            future_to_file = {executor.submit(self.translate_file, file_path): file_path 
                            for file_path in self.detected_files}

            # Process completed translations
            completed = 0
            failed = 0
            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                completed += 1
                try:
                    if not future.result():
                        failed += 1
                except Exception as e:
                    self.console.print(f"[red]Error processing {file_path}: {str(e)}[/red]")
                    failed += 1

                self.console.print(f"Progress: {completed}/{total_files} files processed")

        self.console.print(f"\n[bold]Translation completed: {completed-failed} successful, {failed} failed[/bold]")

    def interactive_mode(self) -> None:
        """
        Interactive mode for file and comment selection
        """
        current_start_index = 0

        while True:
            clear()
            self.display_files(current_start_index)
            command = self.session.prompt("\nEnter command: ").strip().lower()

            if command == 'quit':
                break
            elif command == 'y':
                self.translate_all_files()
                break
            elif command == 'next':
                if current_start_index + self.page_size < len(self.detected_files):
                    current_start_index += self.page_size
                else:
                    self.console.print("[yellow]No more files to display[/yellow]")
            elif command.startswith('show '):
                try:
                    file_index = int(command.split()[1])
                    comment_start = 0
                    while True:
                        clear()
                        self.show_comments(file_index, comment_start)
                        sub_command = self.session.prompt("\nEnter command: ").strip().lower()
                        if sub_command == 'back':
                            break
                        elif sub_command == 'next':
                            comment_start += self.page_size
                        elif sub_command == 'quit':
                            return
                        else:
                            self.console.print("[red]Invalid command. Use 'next', 'back', or 'quit'[/red]")
                except (ValueError, IndexError):
                    self.console.print("[red]Invalid show command. Use 'show [id]'[/red]")
            else:
                self.console.print("[red]Invalid command[/red]")

def main():
    parser = argparse.ArgumentParser(description='Code Comment Translator')
    parser.add_argument('--target', required=True, help='Path to file or directory')
    parser.add_argument('--config', default='config.yaml', help='Path to configuration file')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    translator = CodeCommentTranslator(args.target, args.config, args.debug)
    translator.detect_files()
    translator.interactive_mode()

if __name__ == '__main__':
    main()