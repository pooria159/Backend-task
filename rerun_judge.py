import subprocess
import sys
import json
import re
from datetime import datetime

def main():
    print("اجرای دوباره تست‌های Judge ...\n")

    cmd = [sys.executable, "manage.py", "test", "judge", "--verbosity", "2"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    output = result.stdout

    match = re.search(r'Ran\s+(\d+)\s+tests?.*in\s+([\d\.]+)s', output)
    total_tests = int(match.group(1)) if match else 0
    duration = float(match.group(2)) if match else 0.0

    failed_tests = len(re.findall(r'FAIL:', output))
    errors_count = len(re.findall(r'ERROR:', output))
    passed_tests = total_tests - (failed_tests + errors_count)
    score = round((passed_tests / total_tests) * 100, 2) if total_tests > 0 else 0.0
    success = failed_tests == 0 and errors_count == 0

    result_data = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "errors": errors_count,
        "duration_seconds": duration,
        "score": score,
        "success": success,
    }

    with open("judge_results.json", "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=4)

    print("==========================================")
    print(f" تعداد تست‌ها: {total_tests}")
    print(f" موفق: {passed_tests}")
    print(f" ناموفق: {failed_tests}")
    print(f" خطاها: {errors_count}")
    print(f" زمان اجرا: {duration:.2f} ثانیه")
    print(f" نمره نهایی: {score}%")
    print("==========================================")

    if success:
        print("همه تست‌های با موفقیت پاس شدند")
    else:
        print("برخی تست‌ها رد شدند. لطفاً کد را بررسی کنید.")
        print("\nخروجی تست‌ها:")
        print(output)

if __name__ == "__main__":
    main()
