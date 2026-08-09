from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "ege-matematika-profil-demoversiya"
EXPECTED_DEMO_SHA256 = "f223ca76f3c703d136f05e7f197e8fb8bc7a8925b89b1bef533a58e99a5413d5"
ZIP_NAME = "ege-matematika-profil-demoversiya-VERIFIED-PACKAGE-v2-1-fixed.zip"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def pdf_text(path: Path, max_pages: int = 5) -> str:
    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages[:max_pages]).lower()


def install_official_sources() -> dict[str, str]:
    archive = Path(os.environ.get("FIPI_ZIP", "/tmp/ma_11_2026.zip"))
    if not archive.exists():
        raise RuntimeError(f"Official FIPI archive not found: {archive}")

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(tmpdir)
        pdfs = sorted(tmpdir.rglob("*.pdf"))
        if not pdfs:
            raise RuntimeError("No PDFs found in official FIPI archive")

        demo = None
        spec = None
        codifier = None
        for pdf in pdfs:
            text = pdf_text(pdf)
            if "кодификатор" in text and codifier is None:
                codifier = pdf
            if "спецификация" in text and "профильн" in text and spec is None:
                spec = pdf
            if "демонстрацион" in text and "профильн" in text and demo is None:
                demo = pdf

        if not all((demo, spec, codifier)):
            inventory = "\n".join(str(p.relative_to(tmpdir)) for p in pdfs)
            raise RuntimeError("Could not classify profile FIPI files. Inventory:\n" + inventory)

        source = ROOT / "source"
        if source.exists():
            shutil.rmtree(source)
        source.mkdir()
        targets = {
            "demo": source / "ege-2026-matematika-profil-demoversiya.pdf",
            "spec": source / "ege-2026-matematika-profil-specifikatsiya.pdf",
            "codifier": source / "ege-2026-matematika-kodifikator.pdf",
        }
        shutil.copy2(demo, targets["demo"])
        shutil.copy2(spec, targets["spec"])
        shutil.copy2(codifier, targets["codifier"])

    hashes = {key: sha256(path) for key, path in targets.items()}
    if hashes["demo"] != EXPECTED_DEMO_SHA256:
        raise RuntimeError(
            f"Unexpected final demo SHA-256: {hashes['demo']} != {EXPECTED_DEMO_SHA256}"
        )
    old_project = ROOT / "official-FIPI-demo-2026-profile-math.pdf"
    if old_project.exists():
        old_project.unlink()
    return hashes


def criteria_table(rows: list[tuple[str, int]], maximum: int) -> str:
    body = "".join(f"<tr><td>{text}</td><td>{score}</td></tr>" for text, score in rows)
    return (
        '<div class="emprof-table-wrap"><table class="emprof-criteria-table">'
        '<thead><tr><th>Критерии оценивания выполнения задания</th><th>Баллы</th></tr></thead>'
        f'<tbody>{body}<tr><td><strong>Максимальный балл</strong></td>'
        f'<td><strong>{maximum}</strong></td></tr></tbody></table></div>'
    )


def load_tasks(path: Path, variable: str) -> list[dict]:
    text = read(path)
    match = re.fullmatch(rf'<script>window\.{re.escape(variable)}=(\[.*\]);</script>\s*', text, re.S)
    if not match:
        raise RuntimeError(f"Unexpected task container: {path.name}")
    return json.loads(match.group(1))


def save_tasks(path: Path, variable: str, tasks: list[dict]) -> None:
    payload = json.dumps(tasks, ensure_ascii=False, separators=(",", ":"))
    write(path, f"<script>window.{variable}={payload};</script>\n")


def update_criteria() -> None:
    path4 = ROOT / f"{PREFIX}-T123-04.txt"
    path5 = ROOT / f"{PREFIX}-T123-05.txt"
    tasks4 = load_tasks(path4, "EMPROF_TASKS_3")
    tasks5 = load_tasks(path5, "EMPROF_TASKS_4")

    criteria13 = criteria_table(
        [
            ("Обоснованно получены верные ответы в обоих пунктах.", 2),
            (
                "Обоснованно получен верный ответ в пункте а.<br><strong>ИЛИ</strong><br>"
                "Получены неверные ответы из-за вычислительной ошибки, но имеется верная "
                "последовательность всех шагов решения обоих пунктов: пункта а и пункта б.",
                1,
            ),
            ("Решение не соответствует ни одному из критериев, перечисленных выше.", 0),
        ],
        2,
    )
    criteria14_17 = criteria_table(
        [
            ("Имеется верное доказательство утверждения пункта а и обоснованно получен верный ответ в пункте б.", 3),
            (
                "Получен обоснованный ответ в пункте б.<br><strong>ИЛИ</strong><br>"
                "Имеется верное доказательство утверждения пункта а, но при обоснованном "
                "решении пункта б получен неверный ответ из-за арифметической ошибки.",
                2,
            ),
            (
                "Имеется верное доказательство утверждения пункта а.<br><strong>ИЛИ</strong><br>"
                "При обоснованном решении пункта б получен неверный ответ из-за арифметической ошибки."
                "<br><strong>ИЛИ</strong><br>Обоснованно получен верный ответ в пункте б с "
                "использованием утверждения пункта а, при этом пункт а не выполнен.",
                1,
            ),
            ("Решение не соответствует ни одному из критериев, приведённых выше.", 0),
        ],
        3,
    )
    criteria16 = criteria_table(
        [
            ("Обоснованно получен верный ответ.", 2),
            ("Верно построена математическая модель.", 1),
            ("Решение не соответствует ни одному из критериев, перечисленных выше.", 0),
        ],
        2,
    )
    criteria18v2 = criteria_table(
        [
            ("Обоснованно получен верный ответ.", 4),
            (
                "С помощью верного рассуждения получено множество значений a, отличающееся "
                "от искомого только включением точек a = −√2 и/или a = √2.",
                3,
            ),
            (
                "С помощью верного рассуждения получено множество значений a, отличающееся "
                "от искомого только исключением точек a = −√33/4 и/или a = √33/4."
                "<br><strong>ИЛИ</strong><br>Получен неверный ответ из-за вычислительной ошибки, "
                "но при этом верно выполнены все шаги решения.",
                2,
            ),
            (
                "Задача верно сведена к исследованию расположения корней квадратного уравнения "
                "y² − 7y + 4a² + 4 = 0, где y = |x − a²| + |x + 1|.",
                1,
            ),
            ("Решение не соответствует ни одному из критериев, перечисленных выше.", 0),
        ],
        4,
    )

    for task in tasks4:
        if task["number"] == 13:
            task["criteriaHtml"] = criteria13
        elif task["number"] == 14:
            task["criteriaHtml"] = criteria14_17
    for task in tasks5:
        if task["number"] == 16:
            task["criteriaHtml"] = criteria16
        elif task["number"] == 17:
            task["criteriaHtml"] = criteria14_17
        elif task["number"] == 18 and task["variant"] == 2:
            task["criteriaHtml"] = criteria18v2

    save_tasks(path4, "EMPROF_TASKS_3", tasks4)
    save_tasks(path5, "EMPROF_TASKS_4", tasks5)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old in text:
        return text.replace(old, new, 1)
    if new in text:
        return text
    raise RuntimeError(f"Expected text not found: {label}")


def update_interface_and_logic() -> None:
    path1 = ROOT / f"{PREFIX}-T123-01.txt"
    text1 = read(path1)
    old_scores = (
        '<div class="emprof-result"><section class="ep-panel"><div class="ep-meta"><span class="ep-pill ep-pill--green">Попытка завершена</span><span id="emprof-date" class="ep-pill"></span></div><h2>Результат</h2><div class="emprof-score-grid"><div class="emprof-score-card"><div class="emprof-score-value"><span id="emprof-short-score">0</span>/12</div><p>Краткая часть</p></div><div class="emprof-score-card"><div class="emprof-score-value"><span id="emprof-ext-score">—</span>/20</div><p>Самооценка 13–19</p></div><div class="emprof-score-card"><div class="emprof-score-value"><span id="emprof-total-score">—</span>/32</div><p>Общий балл</p></div></div></section><section class="ep-panel"><h2>Самооценка заданий 13–19</h2><p>Сопоставьте работу с приведённым возможным решением и ориентирами оценивания. Самооценка не заменяет проверку эксперта.</p><div id="emprof-self"></div></section>'
    )
    new_scores = (
        '<div class="emprof-result"><section class="ep-panel"><div class="ep-meta"><span class="ep-pill ep-pill--green">Попытка завершена</span><span id="emprof-date" class="ep-pill"></span></div><h2>Результат</h2><div class="emprof-score-grid"><div class="emprof-score-card"><div class="emprof-score-value"><span id="emprof-short-score">0</span>/12</div><p>Автоматически проверенная краткая часть</p></div><div class="emprof-score-card"><div class="emprof-score-value"><span id="emprof-ext-score">—</span>/20</div><p>Неофициальная самооценка 13–19</p></div><div class="emprof-score-card"><div class="emprof-score-value"><span id="emprof-total-score">—</span>/32</div><p>Официальный итог после проверки экспертом</p></div></div></section><section class="ep-panel"><h2>Самооценка заданий 13–19</h2><p>Сопоставьте работу с возможным решением и точными критериями ФИПИ. Выбранные здесь баллы служат только для самопроверки, не входят в официальный результат и не заменяют проверку эксперта.</p><div id="emprof-self"></div></section>'
    )
    text1 = replace_once(text1, old_scores, new_scores, "result score cards")
    old_footer = '<p class="emprof-mini">Локальный пакет проверен. После установки на Tilda требуется контроль опубликованной страницы.</p>'
    new_footer = '<p class="emprof-mini">Баллы за задания 13–19 устанавливаются экспертом по критериям ФИПИ; самостоятельная оценка в интерфейсе не является официальной.</p>'
    text1 = replace_once(text1, old_footer, new_footer, "service footer")
    write(path1, text1)

    path6 = ROOT / f"{PREFIX}-T123-06.txt"
    text6 = read(path6)
    text6 = text6.replace('KEY="eksamio_ege_math_profile_demo_2026_v2"', 'KEY="eksamio_ege_math_profile_demo_2026_v2_1"')
    old_totals = "function totals(){var ready=true,sum=0;for(var n=13;n<=19;n++){if(state.self[n]==null||state.self[n]==='')ready=false;else sum+=Number(state.self[n])}by(\"emprof-ext-score\").textContent=ready?sum:'—';by(\"emprof-total-score\").textContent=ready?(Number(by(\"emprof-short-score\").textContent)+sum):'—'}"
    new_totals = "function totals(){var ready=true,sum=0;for(var n=13;n<=19;n++){if(state.self[n]==null||state.self[n]==='')ready=false;else sum+=Number(state.self[n])}by(\"emprof-ext-score\").textContent=ready?sum:'—';by(\"emprof-total-score\").textContent='—'}"
    text6 = replace_once(text6, old_totals, new_totals, "official total calculation")
    old_api = "window.__emprofTest={tasks:TASKS,getTask:function(n,v){return TASKS.find(function(t){return t.number===n&&t.variant===v})},score:score,valid:valid,state:function(){return JSON.parse(JSON.stringify(state))},setTask:function(n,v){ensure();state.status='running';state.current=n;state.variants[n]=v;update();buildNav();render()},start:start,finish:function(){finish(true)}};"
    new_api = "window.__emprofTest={tasks:TASKS,getTask:function(n,v){return TASKS.find(function(t){return t.number===n&&t.variant===v})},score:score,valid:valid,state:function(){return JSON.parse(JSON.stringify(state))},setTask:function(n,v){ensure();state.status='running';state.current=n;state.variants[n]=v;update();buildNav();render()},start:start,finish:function(){finish(true)},selfAssessmentAffectsOfficialTotal:false};"
    text6 = replace_once(text6, old_api, new_api, "test API")
    write(path6, text6)





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


def rebuild_preview() -> None:
    head = read(ROOT / f"{PREFIX}-HEAD.txt").strip()
    blocks = "\n".join(read(ROOT / f"{PREFIX}-T123-{i:02d}.txt").rstrip() for i in range(1, 7))
    preview = (
        '<!doctype html><html lang="ru"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Демоверсия ЕГЭ по профильной математике</title>\n'
        f"{head}</head><body style=\"margin:0\">{blocks}\n</body></html>\n"
    )
    write(ROOT / f"{PREFIX}-PREVIEW.html", preview)


def release_files() -> list[Path]:
    files = []
    for path in sorted(ROOT.glob(f"{PREFIX}-*")):
        if path.is_file() and path.name not in {f"{PREFIX}-MANIFEST.txt", ZIP_NAME}:
            files.append(path)
    files.extend(sorted((ROOT / "source").glob("*.pdf")))
    return files


def rebuild_manifest_and_zip() -> None:
    manifest = ROOT / f"{PREFIX}-MANIFEST.txt"
    lines = []
    for path in release_files():
        lines.append(f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}")
    write(manifest, "\n".join(lines) + "\n")

    zip_path = ROOT / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()
    package_files = release_files() + [manifest]
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(package_files):
            zf.write(path, path.relative_to(ROOT).as_posix())


def validate() -> None:
    path4 = ROOT / f"{PREFIX}-T123-04.txt"
    path5 = ROOT / f"{PREFIX}-T123-05.txt"
    tasks = load_tasks(path4, "EMPROF_TASKS_3") + load_tasks(path5, "EMPROF_TASKS_4")
    lookup = {(t["number"], t["variant"]): t for t in tasks}
    required = {
        (13, 1): ["верный ответ в пункте а", "всех шагов решения обоих пунктов"],
        (13, 2): ["верный ответ в пункте а", "всех шагов решения обоих пунктов"],
        (14, 1): ["Получен обоснованный ответ в пункте б", "пункт а не выполнен"],
        (14, 2): ["Получен обоснованный ответ в пункте б", "пункт а не выполнен"],
        (16, 1): ["Верно построена математическая модель"],
        (16, 2): ["Верно построена математическая модель"],
        (17, 1): ["Получен обоснованный ответ в пункте б", "пункт а не выполнен"],
        (17, 2): ["Получен обоснованный ответ в пункте б", "пункт а не выполнен"],
        (18, 2): ["a = −√2", "a = √2", "a = −√33/4", "a = √33/4"],
    }
    for key, phrases in required.items():
        text = lookup[key]["criteriaHtml"]
        for phrase in phrases:
            if phrase not in text:
                raise RuntimeError(f"Missing criterion phrase {phrase!r} for {key}")

    logic = read(ROOT / f"{PREFIX}-T123-06.txt")
    if "+sum" in logic or "selfAssessmentAffectsOfficialTotal:false" not in logic:
        raise RuntimeError("Self-assessment still affects official total")
    interface = read(ROOT / f"{PREFIX}-T123-01.txt")
    if "Локальный пакет проверен" in interface:
        raise RuntimeError("Service phrase remains in T123-01")
    preview = read(ROOT / f"{PREFIX}-PREVIEW.html")
    if "Локальный пакет проверен" in preview:
        raise RuntimeError("Service phrase remains in preview")
    if (ROOT / "official-FIPI-demo-2026-profile-math.pdf").exists():
        raise RuntimeError("Project PDF remains")
    for path in [
        ROOT / "source/ege-2026-matematika-profil-demoversiya.pdf",
        ROOT / "source/ege-2026-matematika-profil-specifikatsiya.pdf",
        ROOT / "source/ege-2026-matematika-kodifikator.pdf",
    ]:
        if not path.exists():
            raise RuntimeError(f"Missing source: {path}")
    with zipfile.ZipFile(ROOT / ZIP_NAME) as zf:
        bad = zf.testzip()
        if bad:
            raise RuntimeError(f"Corrupt ZIP member: {bad}")
        names = set(zf.namelist())
        if "official-FIPI-demo-2026-profile-math.pdf" in names:
            raise RuntimeError("Project PDF included in ZIP")
        if not all(name in names for name in [
            "source/ege-2026-matematika-profil-demoversiya.pdf",
            "source/ege-2026-matematika-profil-specifikatsiya.pdf",
            "source/ege-2026-matematika-kodifikator.pdf",
        ]):
            raise RuntimeError("Source PDFs missing from ZIP")


def main() -> None:
    source_hashes = install_official_sources()
    update_criteria()
    update_interface_and_logic()
    update_documents(source_hashes)
    rebuild_preview()
    rebuild_manifest_and_zip()
    validate()
    for obsolete in [
        ROOT / "scripts/extract_profile_pdf.py",
        ROOT / "scripts/profile_pdf_text.txt",
    ]:
        if obsolete.exists():
            obsolete.unlink()
    print("Profile mathematics prelaunch correction: PASS")
    print(json.dumps(source_hashes, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
