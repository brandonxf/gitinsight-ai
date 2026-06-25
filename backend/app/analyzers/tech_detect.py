"""Detección de lenguajes, frameworks y dependencias a partir de manifiestos."""
from __future__ import annotations

import json
import tomllib
from pathlib import Path

from app.analyzers.base import AnalysisContext, Analyzer, AnalyzerResult

# Pistas de framework por dependencia (substring del nombre -> etiqueta legible).
_PY_FRAMEWORKS = {
    "fastapi": "FastAPI", "django": "Django", "flask": "Flask",
    "starlette": "Starlette", "celery": "Celery", "sqlalchemy": "SQLAlchemy",
    "pydantic": "Pydantic", "tornado": "Tornado", "aiohttp": "aiohttp",
    "pytest": "pytest", "numpy": "NumPy", "pandas": "pandas",
    "torch": "PyTorch", "tensorflow": "TensorFlow", "scikit-learn": "scikit-learn",
}
_JS_FRAMEWORKS = {
    "react": "React", "next": "Next.js", "vue": "Vue", "nuxt": "Nuxt",
    "svelte": "Svelte", "@angular/core": "Angular", "express": "Express",
    "nestjs": "NestJS", "@nestjs/core": "NestJS", "fastify": "Fastify",
    "vite": "Vite", "webpack": "Webpack", "tailwindcss": "TailwindCSS",
    "typescript": "TypeScript", "jest": "Jest", "vitest": "Vitest",
}


def _match_frameworks(deps: list[str], table: dict[str, str]) -> set[str]:
    found: set[str] = set()
    lowered = [d.lower() for d in deps]
    for key, label in table.items():
        if any(key in dep for dep in lowered):
            found.add(label)
    return found


class TechDetectAnalyzer(Analyzer):
    name = "tech_detect"

    def run(self, context: AnalysisContext) -> AnalyzerResult:
        languages: dict[str, int] = {}
        for f in context.files:
            if f.language:
                languages[f.language] = languages.get(f.language, 0) + 1

        frameworks: set[str] = set()
        package_managers: set[str] = set()
        root = context.repo_path

        self._detect_python(root, frameworks, package_managers)
        self._detect_node(root, frameworks, package_managers)
        self._detect_misc(root, frameworks, package_managers)

        primary_language = max(languages, key=languages.get) if languages else None
        context.shared["primary_language"] = primary_language
        context.shared["languages"] = languages

        return AnalyzerResult(
            data={
                "primary_language": primary_language,
                "languages": languages,
                "frameworks": sorted(frameworks),
                "package_managers": sorted(package_managers),
            }
        )

    def _detect_python(self, root: Path, frameworks: set[str], pms: set[str]) -> None:
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            pms.add("pip/pyproject")
            try:
                data = tomllib.loads(pyproject.read_text(encoding="utf-8", errors="ignore"))
            except (tomllib.TOMLDecodeError, OSError):
                data = {}
            deps: list[str] = []
            project = data.get("project", {})
            deps += [str(d) for d in project.get("dependencies", [])]
            for group in project.get("optional-dependencies", {}).values():
                deps += [str(d) for d in group]
            poetry = data.get("tool", {}).get("poetry", {})
            deps += list(poetry.get("dependencies", {}).keys())
            if poetry:
                pms.add("poetry")
            frameworks |= _match_frameworks(deps, _PY_FRAMEWORKS)

        requirements = root / "requirements.txt"
        if requirements.exists():
            pms.add("pip")
            try:
                lines = requirements.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                lines = []
            deps = [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]
            frameworks |= _match_frameworks(deps, _PY_FRAMEWORKS)

    def _detect_node(self, root: Path, frameworks: set[str], pms: set[str]) -> None:
        package_json = root / "package.json"
        if not package_json.exists():
            return
        pms.add("npm")
        try:
            data = json.loads(package_json.read_text(encoding="utf-8", errors="ignore"))
        except (json.JSONDecodeError, OSError):
            return
        deps = list(data.get("dependencies", {}).keys())
        deps += list(data.get("devDependencies", {}).keys())
        frameworks |= _match_frameworks(deps, _JS_FRAMEWORKS)
        if (root / "pnpm-lock.yaml").exists():
            pms.add("pnpm")
        if (root / "yarn.lock").exists():
            pms.add("yarn")

    def _detect_misc(self, root: Path, frameworks: set[str], pms: set[str]) -> None:
        manifest_signals = {
            "go.mod": ("Go modules", "Go"),
            "Cargo.toml": ("Cargo", "Rust"),
            "pom.xml": ("Maven", "Java"),
            "build.gradle": ("Gradle", "Java"),
            "composer.json": ("Composer", "PHP"),
            "Gemfile": ("Bundler", "Ruby"),
        }
        for filename, (pm, framework) in manifest_signals.items():
            if (root / filename).exists():
                pms.add(pm)
                frameworks.add(framework)
        if (root / "Dockerfile").exists() or (root / "docker-compose.yml").exists():
            frameworks.add("Docker")
