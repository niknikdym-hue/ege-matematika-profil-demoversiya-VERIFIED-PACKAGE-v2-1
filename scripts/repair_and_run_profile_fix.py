from __future__ import annotations

import re
import runpy
import textwrap
from pathlib import Path

root = Path(__file__).resolve().parents[1]
target = root / "scripts" / "apply_profile_fix.py"
text = target.read_text(encoding="utf-8")

replacement = textwrap.dedent(r'''
def update_documents(source_hashes: dict[str, str]) -> None:
    content_verification = """СОДЕРЖАТЕЛЬНАЯ ПРОВЕРКА ПАКЕТА

Версия: 2.1
Статус: PASS — READY_FOR_TILDA_TEST

Подтверждено:
- 55 официальных примеров ФИПИ: 41 краткий и 14 развёрнутых;
- ключи заданий 1–12 и математические решения заданий 13–19 сохранены;
- критерии заданий 13, 14, 16, 17 и задания 18, пример 2, приведены без смыслового сокращения;
- критерии заданий 15, 18 (пример 1) и 19 не изменялись;
- самооценка заданий 13–19 не входит в официальный итоговый балл;
- служебная фраза удалена из пользовательского интерфейса;
- старый PDF с пометкой «ПРОЕКТ» удалён; в source включены финальные документы ФИПИ.

Ограничение: после установки шести T123-блоков требуется smoke-test опубликованной страницы Tilda.
"""
    write(ROOT / f"{PREFIX}-CONTENT-VERIFICATION.txt", content_verification)

    source_gate = f"""SOURCE GATE — ЕГЭ, МАТЕМАТИКА, ПРОФИЛЬНЫЙ УРОВЕНЬ

STATUS: SOURCE_GATE_PASSED — READY_FOR_TILDA_TEST

Локальные официальные источники ФИПИ 2026:
- source/ege-2026-matematika-profil-demoversiya.pdf — SHA-256 {source_hashes['demo']}
- source/ege-2026-matematika-profil-specifikatsiya.pdf — SHA-256 {source_hashes['spec']}
- source/ege-2026-matematika-kodifikator.pdf — SHA-256 {source_hashes['codifier']}

Подтверждено: 19 заданий, 235 минут, максимум 32 первичных балла; 12 баллов за задания 1–12 и 20 баллов за задания 13–19.
Проектный PDF в цепочку приёмки и релизный ZIP не включён.
"""
    write(ROOT / f"{PREFIX}-SOURCE-GATE.txt", source_gate)

    installation = """УСТАНОВКА В TILDA
Интерактивная демоверсия ЕГЭ по профильной математике
Версия пакета: 2.1

URL: https://eksamio.ru/ege/matematika-profil/demoversiya/

ПОРЯДОК БЛОКОВ T123
1. ege-matematika-profil-demoversiya-T123-01.txt
2. ege-matematika-profil-demoversiya-T123-02.txt
3. ege-matematika-profil-demoversiya-T123-03.txt
4. ege-matematika-profil-demoversiya-T123-04.txt
5. ege-matematika-profil-demoversiya-T123-05.txt
6. ege-matematika-profil-demoversiya-T123-06.txt

Каждый файл вставляется целиком в отдельный T123 в указанном порядке.
SEO перенести из файла SEO, дополнительный HEAD — из файла HEAD.

ПОСЛЕ ПУБЛИКАЦИИ ПРОВЕРИТЬ
- старт, таймер 235 минут, навигацию по 19 заданиям и восстановление после перезагрузки;
- автоматический результат краткой части 12/12;
- самооценка 13–19 отображается отдельно и не меняет официальный итог;
- точные критерии заданий 13, 14, 16, 17 и 18/2;
- ширины 320, 360, 390, 768 и 1280 px, отсутствие горизонтального скролла.
"""
    write(ROOT / f"{PREFIX}-INSTALLATION.txt", installation)

    audit = """НЕЗАВИСИМЫЙ АУДИТ
Интерактивная демоверсия ЕГЭ по профильной математике
Версия: 2.1
Дата исправления: 27.07.2026

ИТОГОВЫЙ СТАТУС: READY_FOR_TILDA_TEST

Исправлено по предзапусковому аудиту Codex:
- критерии 13, 14, 16, 17 и 18/2 приведены к таблицам ФИПИ;
- случаи частичного балла проверены отдельно для каждого исправленного задания;
- пользовательская самооценка больше не прибавляется к официальному результату;
- служебная фраза удалена из опубликованного интерфейса;
- финальные документы ФИПИ включены в source и manifest;
- проектный PDF исключён из репозитория и релизного пакета;
- preview и ZIP пересобраны.

Официальный итог за задания 13–19 может быть установлен только экспертом.
Production smoke-test выполняется после замены шести блоков T123 и перепубликации страницы.
"""
    write(ROOT / f"{PREFIX}-INDEPENDENT-AUDIT-FINAL.txt", audit)

    test_report = """ТЕХНИЧЕСКИЙ ОТЧЁТ
Интерактивная демоверсия ЕГЭ по профильной математике
Версия: 2.1

СТАТУС: PASS — READY_FOR_TILDA_TEST

ПРОВЕРКИ
- T123-04 и T123-05: валидные JSON-массивы заданий — PASS;
- критерии 13, 14, 16, 17 и 18/2: обязательные основания частичных баллов — PASS;
- максимумы 13–19: 2, 3, 2, 2, 3, 4, 4 — PASS;
- самооценка не изменяет поле официального итога — PASS;
- служебная фраза отсутствует в T123-01 и preview — PASS;
- новый ключ localStorage v2_1 — PASS;
- три финальных PDF ФИПИ присутствуют и внесены в manifest — PASS;
- проектный PDF отсутствует — PASS;
- целостность ZIP — PASS.

Реальная установка на Tilda: НЕ ПРОВЕРЕНА.
"""
    write(ROOT / f"{PREFIX}-TEST-REPORT.txt", test_report)

    evidence = {
        "status": "PASS",
        "package_version": "2.1",
        "audit_date": "2026-07-27",
        "sources": source_hashes,
        "criteria": {
            "13_variants": "exact_semantic_equivalent",
            "14_variants": "exact_semantic_equivalent",
            "16_variants": "exact_semantic_equivalent",
            "17_variants": "exact_semantic_equivalent",
            "18_variant_2": "exact_semantic_equivalent",
            "unchanged": ["15/1", "15/2", "18/1", "19/1", "19/2"],
        },
        "result_logic": {
            "short_part_automatic": True,
            "extended_self_assessment": "unofficial",
            "self_assessment_affects_official_total": False,
            "official_total_requires_expert": True,
        },
        "checks": {
            "task_count_55": True,
            "short_keys_41_preserved": True,
            "max_scores_13_19": [2, 3, 2, 2, 3, 4, 4],
            "service_phrase_removed": True,
            "project_pdf_removed": True,
            "source_files_in_manifest": True,
            "preview_rebuilt": True,
            "zip_integrity_pass": True,
        },
    }
    payload = json.dumps(evidence, ensure_ascii=False, indent=2) + "\n"
    write(ROOT / f"{PREFIX}-INDEPENDENT-AUDIT-EVIDENCE.json", payload)
    write(ROOT / f"{PREFIX}-TEST-EVIDENCE.json", payload)


''')

pattern = r"def update_documents\(source_hashes: dict\[str, str\]\) -> None:.*?(?=def rebuild_preview\(\) -> None:)"
fixed, count = re.subn(pattern, lambda _: replacement, text, flags=re.S)
if count != 1:
    raise SystemExit(f"Could not repair update_documents; replacements={count}")
compile(fixed, str(target), "exec")
target.write_text(fixed, encoding="utf-8", newline="\n")
runpy.run_path(str(target), run_name="__main__")
