#!/usr/bin/env python3
import subprocess
import sys
import re
import os

def run_git_command(args):
    """Run a git command and return output."""
    try:
        result = subprocess.run(['git'] + args, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running git command: {e}", file=sys.stderr)
        return None

def get_changed_files(base_branch):
    """Get list of changed files between current HEAD and base branch."""
    return run_git_command(['diff', '--name-only', base_branch, 'HEAD']).split('\n')

def get_file_content(filename):
    """Read file content."""
    try:
        with open(filename, 'r') as f:
            return f.read()
    except Exception:
        return ""

def identify_impacted_endpoints(files):
    """Scan files for Controller annotations or Proto definitions."""
    endpoints = []
    
    for file in files:
        if not file: continue
        
        content = get_file_content(file)
        if not content: continue

        # Java Spring Controllers
        if file.endswith('.java'):
            # Simple regex to find mappings. 
            # Note: This is a rough heuristic.
            mappings = re.findall(r'@(Get|Post|Put|Delete|Patch|Request)Mapping\s*\((?:value\s*=\s*)?"([^"]+)"', content)
            
            # Check for class level mapping
            class_mapping = re.search(r'@RequestMapping\s*\((?:value\s*=\s*)?"([^"]+)"', content)
            base_path = class_mapping.group(1) if class_mapping else ""

            for method, path in mappings:
                full_path = f"{base_path}{path}".replace('//', '/')
                endpoints.append({
                    'type': 'REST',
                    'method': method.upper(),
                    'path': full_path,
                    'file': file
                })

        # Proto files
        elif file.endswith('.proto'):
            services = re.findall(r'service\s+(\w+)\s*{', content)
            rpcs = re.findall(r'rpc\s+(\w+)\s*\(', content)
            
            for service in services:
                endpoints.append({
                    'type': 'gRPC',
                    'method': 'Service',
                    'path': service,
                    'file': file
                })
            for rpc in rpcs:
                endpoints.append({
                    'type': 'gRPC',
                    'method': 'RPC',
                    'path': rpc,
                    'file': file
                })

    return endpoints

def generate_title(base_branch):
    """Generate a PR title based on commit frequency and type."""
    commits = run_git_command(['log', f'{base_branch}..HEAD', '--pretty=format:%s'])
    if not commits:
        return "chore: update"
    
    commit_lines = commits.split('\n')
    
    # Priority of types
    type_priority = ['feat', 'fix', 'refactor', 'perf', 'style', 'test', 'chore', 'docs']
    
    counts = {}
    last_msg = {}
    
    for msg in commit_lines:
        match = re.match(r'^(\w+)(?:\(.*\))?: (.+)$', msg)
        if match:
            ctype = match.group(1).lower()
            subject = match.group(2)
            counts[ctype] = counts.get(ctype, 0) + 1
            if ctype not in last_msg:
                last_msg[ctype] = subject
        else:
            # Handle non-conventional commits optionally
            pass

def generate_title(base_branch):
    """Generate a comprehensive PR title."""
    commits = run_git_command(['log', f'{base_branch}..HEAD', '--pretty=format:%s'])
    if not commits:
        return "유지보수 및 업데이트"
    
    commit_lines = commits.split('\n')
    significant_subjects = []
    seen = set()
    
    # Priority types to look for
    target_types = ['feat', 'fix', 'refactor', 'perf']
    
    for msg in commit_lines:
        match = re.match(r'^(\w+)(?:\(.*\))?: (.+)$', msg)
        if match:
            ctype = match.group(1).lower()
            subject = match.group(2)
            if ctype in target_types:
                # Translate
                translated = translate_to_korean(subject)
                if translated not in seen:
                    significant_subjects.append(translated)
                    seen.add(translated)
    
    # If no significant conventional commits, look at first line
    if not significant_subjects:
        first_msg = commit_lines[0]
        match = re.match(r'^\w+(?:\(.*\))?: (.+)$', first_msg)
        if match:
            return translate_to_korean(match.group(1))
        return translate_to_korean(first_msg)
        
    # Detect JIRA Ticket
    jira_ticket = None
    # Look for patterns like PROJECT-123 or #123
    # Prioritize PROJECT-123 over #123
    jira_pattern = re.compile(r'([A-Z]+-\d+)')
    
    for msg in commit_lines:
        match = jira_pattern.search(msg)
        if match:
            jira_ticket = match.group(1)
            break
            
    # Group by Verb (Suffix)
    # Assumes translated subjects end with a verb like '추가', '수정', etc.
    verb_groups = {}
    
    # Common Korean verbs we used in translation
    known_verbs = ['추가', '생성', '업데이트', '수정', '변경', '제거', '삭제', '리팩토링', '구현', '사용', '이동', '이름 변경']
    
    fallback_subjects = []
    
    for subj in significant_subjects:
        matched_verb = None
        for v in known_verbs:
            if subj.endswith(" " + v):
                matched_verb = v
                obj = subj[:-len(v)].strip()
                if matched_verb not in verb_groups:
                    verb_groups[matched_verb] = []
                verb_groups[matched_verb].append(obj)
                break
        
        if not matched_verb:
            # Try to match verb exactly if the subject IS the verb (rare)
            if subj in known_verbs:
                pass # ignore?
            else:
                fallback_subjects.append(subj)
                
    # Construct sentence
    parts = []
    
    for verb, objects in verb_groups.items():
        # Join objects with comma
        obj_str = ", ".join(objects)
        parts.append(f"{obj_str} {verb}")
        
    # Add fallbacks
    parts.extend(fallback_subjects)
    
    if not parts:
        # Fallback to first significant subject or original first line
         full_title = significant_subjects[0] if significant_subjects else translate_to_korean(commit_lines[0].split('\n')[0])
    else:
        # Join parts with " 및 "
        full_title = " 및 ".join(parts)
        
    # Prepend JIRA Ticket
    if jira_ticket:
        return f"[{jira_ticket}] {full_title}"
    else:
        return full_title


def translate_to_korean(text):
    """Simple rule-based translation for commit messages."""
    text = text.strip()
    
    # Check if already distinctively Korean (contains Hangul)
    if re.search(r'[가-힣]', text):
        return text
        
    # Dictionary of verbs and their Korean equivalents (and sentence structure type)
    # Type 1: Verb Object -> Object Verb
    verbs = {
        'add': '추가',
        'create': '생성',
        'update': '업데이트',
        'modify': '수정',
        'change': '변경',
        'remove': '제거',
        'delete': '삭제',
        'fix': '수정',
        'refactor': '리팩토링',
        'implement': '구현',
        'use': '사용',
        'move': '이동',
        'rename': '이름 변경'
    }
    
    # Normalize
    lower_text = text.lower()
    
    for verb, kor_verb in verbs.items():
        # Match "Verb remaining..."
        if lower_text.startswith(verb + " "):
            # Extract object (rest of string)
            obj = text[len(verb):].strip()
            return f"{obj} {kor_verb}"
            
    return text

def generate_commit_summary(base_branch):
    """Group commits by type and return markdown."""
    commits = run_git_command(['log', f'{base_branch}..HEAD', '--pretty=format:%s'])
    if not commits:
        return "커밋 내역이 없습니다.\n"
        
    lines = commits.split('\n')
    groups = {
        'feat': [], 'fix': [], 'refactor': [], 'perf': [], 
        'style': [], 'test': [], 'chore': [], 'docs': [], 'other': []
    }
    
    seen = set()
    
    for line in lines:
        if line in seen: continue
        seen.add(line)
        
        match = re.match(r'^(\w+)(?:\(.*\))?: (.+)$', line)
        if match:
            ctype = match.group(1).lower()
            subject = match.group(2)
            if ctype in groups:
                groups[ctype].append(subject)
            else:
                groups['other'].append(line)
        else:
            groups['other'].append(line)
            
    md = "## 🔍 변경 사항\n"
    
    all_items = []
    # Collect significant changes
    for ctype in ['feat', 'fix', 'refactor', 'perf']:
        for item in groups[ctype]:
            # Translate and clean up
            translated = translate_to_korean(item)
            all_items.append(translated)
                
    if all_items:
        for item in all_items:
            md += f"- {item}\n"
    else:
        md += "주요 변경 사항이 없습니다.\n"
    
    md += "\n"
    return md

def generate_file_summary(changed_files):
    """Summarize file changes by module/directory."""
    modules = {}
    critical_files = []
    
    critical_patterns = [r'.*\.gradle', r'.*\.yml', r'.*\.yaml', r'Dockerfile', r'.*\.proto']
    
    for f in changed_files:
        if not f: continue
        
        # Check critical
        is_critical = any(re.match(p, f) for p in critical_patterns)
        if is_critical:
            critical_files.append(f)
            
        # Group by top-level or second-level
        parts = f.split('/')
        if len(parts) > 1:
            module = parts[0]
            modules[module] = modules.get(module, 0) + 1
        else:
            modules['root'] = modules.get('root', 0) + 1
            
    md = ""
    
    # Module Summary
    if modules:
        md += "**모듈별 변경 요약**\n"
        summary_parts = []
        for mod, count in modules.items():
            summary_parts.append(f"{mod} ({count})")
        md += ", ".join(summary_parts) + "\n\n"
        
    # Critical Files
    if critical_files:
        md += "**⚠️ 주요 변경 파일**\n"
        for cf in critical_files:
            md += f"- `{cf}`\n"
    
    return md

def generate_markdown(base_branch, changed_files, endpoints):
    """Generate the PR description markdown."""
    
    # Generate Title first
    title = generate_title(base_branch)
    
    # Generate grouped commits
    commit_summary = generate_commit_summary(base_branch)
    
    # Generate file summary
    file_summary = generate_file_summary(changed_files)
    
    # Output Title preamble
    md = f"TITLE: {title}\n\n"
    
    # md += "# Pull Request\n\n"  <-- Removed
    # md += "## 📝 요약\n"      <-- Removed
    
    # md += "## 🔍 변경 사항\n" <-- Moved inside generate_commit_summary to control empty state better
    md += commit_summary
    
    md += "## 🛠 변경된 파일\n"
    md += file_summary
    md += "\n"

    md += "## 🔌 영향받는 엔드포인트\n"
    if endpoints:
        md += "| 타입 | 메서드/서비스 | 경로/RPC | 소스 |\n"
        md += "| --- | --- | --- | --- |\n"
        for ep in endpoints:
            md += f"| {ep['type']} | {ep['method']} | `{ep['path']}` | `{ep['file']}` |\n"
    else:
        md += "변경된 API 엔드포인트가 감지되지 않았습니다.\n"
    md += "\n"

    md += "## ✅ 체크리스트\n"
    md += "- [ ] 테스트 코드 추가/업데이트\n"
    md += "- [ ] 기술 문서 업데이트\n"
    
    return md

def main():
    # Detect base branch (simple logic: main or develop)
    branches = run_git_command(['branch', '-r'])
    base_branch = 'origin/main'
    if 'origin/develop' in branches:
        base_branch = 'origin/develop'
    
    # Allow override
    if len(sys.argv) > 1:
        base_branch = sys.argv[1]

    print(f"Generating PR body comparing against {base_branch}...", file=sys.stderr)

    changed_files = get_changed_files(base_branch)
    endpoints = identify_impacted_endpoints(changed_files)
    
    markdown = generate_markdown(base_branch, changed_files, endpoints)
    print(markdown)

if __name__ == "__main__":
    main()
