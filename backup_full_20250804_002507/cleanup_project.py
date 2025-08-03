#!/usr/bin/env python3
"""
프로젝트 정리 스크립트
안전하게 중복 파일 제거 및 구조 개선
"""
import os
import shutil
import datetime
from pathlib import Path
import json

class ProjectCleaner:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "backup" / datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.dry_run = True
        self.actions = []
        
    def log_action(self, action_type, source, target=None):
        """작업 로깅"""
        action = {
            "type": action_type,
            "source": str(source),
            "target": str(target) if target else None,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.actions.append(action)
        
        if self.dry_run:
            print(f"[DRY-RUN] {action_type}: {source}" + (f" -> {target}" if target else ""))
        else:
            print(f"[EXECUTE] {action_type}: {source}" + (f" -> {target}" if target else ""))
    
    def backup_file(self, file_path):
        """파일 백업"""
        source = Path(file_path)
        if not source.exists():
            return
            
        backup_path = self.backup_dir / source.name
        
        if not self.dry_run:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, backup_path)
            
        self.log_action("BACKUP", source, backup_path)
        
    def remove_file(self, file_path):
        """파일 제거"""
        source = Path(file_path)
        if not source.exists():
            return
            
        self.backup_file(source)
        
        if not self.dry_run:
            source.unlink()
            
        self.log_action("REMOVE", source)
        
    def move_file(self, source_path, target_dir):
        """파일 이동"""
        source = Path(source_path)
        if not source.exists():
            return
            
        target = Path(target_dir) / source.name
        
        if not self.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))
            
        self.log_action("MOVE", source, target)
        
    def create_directory(self, dir_path):
        """디렉토리 생성"""
        target = Path(dir_path)
        
        if not self.dry_run:
            target.mkdir(parents=True, exist_ok=True)
            
        self.log_action("CREATE_DIR", target)
        
    def phase1_remove_duplicates(self):
        """Phase 1: 중복 파일 제거"""
        print("\n=== Phase 1: 중복 파일 제거 ===")
        
        # 오타 파일
        self.remove_file("gird_cell.py")
        
        # Monitor Manager 중복
        self.remove_file("monitor_manager_fix.py")
        self.remove_file("fix_monitor_manager.py")
        
        # 구버전 파일
        self.remove_file("main.py")
        self.remove_file("ocr_overlay.py")
        
        # 임시 체크 파일
        self.remove_file("check_files.py")
        self.remove_file("check_files_simple.py")
        self.remove_file("simple_test.py")
        
    def phase2_organize_tests(self):
        """Phase 2: 테스트 파일 정리"""
        print("\n=== Phase 2: 테스트 파일 정리 ===")
        
        self.create_directory("tests")
        
        test_files = [
            "test_basic_structure.py",
            "test_refactored_system.py",
            "test_enhanced_detection.py",
            "test_integration.py",
            "test_ocr_detection.py"
        ]
        
        for test_file in test_files:
            if Path(test_file).exists():
                self.move_file(test_file, "tests")
                
    def phase3_organize_tools(self):
        """Phase 3: 도구 파일 정리"""
        print("\n=== Phase 3: 도구 파일 정리 ===")
        
        self.create_directory("tools")
        
        tool_files = [
            "verify_screen_coordinates.py",
            "visual_cell_overlay.py",
            "adjust_coordinates.py"
        ]
        
        for tool_file in tool_files:
            if Path(tool_file).exists():
                self.move_file(tool_file, "tools")
                
    def phase4_create_structure(self):
        """Phase 4: 프로젝트 구조 생성"""
        print("\n=== Phase 4: 프로젝트 구조 생성 ===")
        
        # 디렉토리 구조 생성
        directories = [
            "src/core",
            "src/ocr", 
            "src/monitoring",
            "src/automation",
            "src/gui",
            "docs"
        ]
        
        for directory in directories:
            self.create_directory(directory)
            
        # 파일 이동 매핑
        file_mappings = {
            # Core
            "config_manager.py": "src/core/",
            "service_container.py": "src/core/",
            "grid_manager.py": "src/core/",
            
            # OCR
            "enhanced_ocr_service.py": "src/ocr/",
            "enhanced_ocr_corrector.py": "src/ocr/",
            "ocr_service.py": "src/ocr/",
            
            # Monitoring
            "improved_monitoring_thread.py": "src/monitoring/",
            "monitor_manager.py": "src/monitoring/",
            
            # Automation
            "automation_service.py": "src/automation/",
            "smart_input_automation.py": "src/automation/",
            
            # GUI
            "optimized_chatbot_system.py": "src/gui/",
            "grid_overlay_system.py": "src/gui/",
            "complete_chatbot_system.py": "src/gui/",
            "fixed_gui_system.py": "src/gui/",
            
            # Docs
            "cleanup_report.md": "docs/"
        }
        
        for source_file, target_dir in file_mappings.items():
            if Path(source_file).exists():
                self.move_file(source_file, target_dir)
                
    def create_init_files(self):
        """__init__.py 파일 생성"""
        print("\n=== __init__.py 파일 생성 ===")
        
        init_dirs = [
            "src",
            "src/core",
            "src/ocr",
            "src/monitoring", 
            "src/automation",
            "src/gui",
            "tests",
            "tools"
        ]
        
        for init_dir in init_dirs:
            init_file = Path(init_dir) / "__init__.py"
            
            if not self.dry_run:
                init_file.parent.mkdir(parents=True, exist_ok=True)
                init_file.touch()
                
            self.log_action("CREATE", init_file)
            
    def save_cleanup_log(self):
        """정리 작업 로그 저장"""
        log_file = self.backup_dir / "cleanup_log.json"
        
        if not self.dry_run:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": datetime.datetime.now().isoformat(),
                    "dry_run": self.dry_run,
                    "actions": self.actions
                }, f, indent=2, ensure_ascii=False)
                
        print(f"\n로그 저장: {log_file}")
        
    def run(self, dry_run=True, phases=None):
        """정리 실행"""
        self.dry_run = dry_run
        self.actions = []
        
        if phases is None:
            phases = [1, 2, 3, 4]
            
        print(f"\n{'='*60}")
        print(f"프로젝트 정리 {'[DRY-RUN]' if dry_run else '[EXECUTE]'}")
        print(f"{'='*60}")
        
        if 1 in phases:
            self.phase1_remove_duplicates()
        if 2 in phases:
            self.phase2_organize_tests()
        if 3 in phases:
            self.phase3_organize_tools()
        if 4 in phases:
            self.phase4_create_structure()
            self.create_init_files()
            
        self.save_cleanup_log()
        
        print(f"\n총 {len(self.actions)}개 작업 {'계획됨' if dry_run else '완료됨'}")
        
        if dry_run:
            print("\n실제로 실행하려면: python cleanup_project.py --execute")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="프로젝트 정리 도구")
    parser.add_argument("--execute", action="store_true", help="실제로 정리 실행 (기본값: dry-run)")
    parser.add_argument("--phase", type=int, nargs='+', choices=[1, 2, 3, 4],
                       help="실행할 단계 선택 (기본값: 모든 단계)")
    
    args = parser.parse_args()
    
    cleaner = ProjectCleaner()
    cleaner.run(dry_run=not args.execute, phases=args.phase)
    
    if not args.execute:
        print("\n⚠️  주의: 실제 실행 전 반드시 백업하세요!")
        print("백업 명령: xcopy . .\\backup_full /E /I /Y")


if __name__ == "__main__":
    main()