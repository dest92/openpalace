"""Next.js framework enhancer for extracting framework-specific metadata."""

from pathlib import Path
from typing import Dict, List, Optional, Any
import json


class NextJSEnhancer:
    """
    Enhancer for Next.js framework-specific metadata.

    Detects Next.js projects and extracts route information
    from /pages/, /app/, and /pages/api/ directories.
    """

    def __init__(self, project_root: Path):
        """
        Initialize Next.js enhancer.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self._router_type = None
        self._is_nextjs = None

    def is_nextjs_project(self) -> bool:
        """
        Check if this is a Next.js project.

        Returns:
            True if next.config.js or next.config.ts exists
        """
        if self._is_nextjs is not None:
            return self._is_nextjs

        config_files = [
            "next.config.js",
            "next.config.mjs",
            "next.config.ts",
            "next.config.mts"
        ]

        self._is_nextjs = any(
            (self.project_root / f).exists()
            for f in config_files
        )

        return self._is_nextjs

    def get_router_type(self) -> Optional[str]:
        """
        Detect which Next.js router is being used.

        Returns:
            "pages" for Pages router, "app" for App router, or None
        """
        if not self.is_nextjs_project():
            return None

        if self._router_type is not None:
            return self._router_type

        # Check for App Router (takes precedence)
        app_dir = self.project_root / "app"
        if app_dir.exists() and app_dir.is_dir():
            # Check if it has route files
            has_routes = any(
                f.suffix in ['.js', '.jsx', '.ts', '.tsx']
                for f in app_dir.rglob('*')
                if f.is_file()
            )
            if has_routes:
                self._router_type = "app"
                return "app"

        # Check for Pages Router
        pages_dir = self.project_root / "pages"
        if pages_dir.exists() and pages_dir.is_dir():
            # Check if it has route files
            has_routes = any(
                f.suffix in ['.js', '.jsx', '.ts', '.tsx']
                for f in pages_dir.rglob('*')
                if f.is_file()
            )
            if has_routes:
                self._router_type = "pages"
                return "pages"

        self._router_type = None
        return None

    def extract_routes(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract all routes from the Next.js project.

        Returns:
            Dict with 'pages', 'app', and 'api' route lists
        """
        routes = {
            "pages": [],
            "app": [],
            "api": []
        }

        if not self.is_nextjs_project():
            return routes

        router_type = self.get_router_type()

        # Extract App Router routes
        if router_type == "app" or router_type is None:
            routes["app"] = self._extract_app_routes()

        # Extract Pages Router routes
        if router_type == "pages" or router_type is None:
            routes["pages"] = self._extract_pages_routes()
            routes["api"] = self._extract_api_routes()

        return routes

    def _extract_app_routes(self) -> List[Dict[str, Any]]:
        """
        Extract routes from /app directory (App Router).

        Returns:
            List of route metadata dicts
        """
        routes = []
        app_dir = self.project_root / "app"

        if not app_dir.exists():
            return routes

        for file_path in app_dir.rglob('*'):
            if not file_path.is_file():
                continue

            if file_path.suffix not in ['.js', '.jsx', '.ts', '.tsx']:
                continue

            # Extract route path from file path
            route_path = self._get_app_route_path(file_path, app_dir)

            routes.append({
                "path": route_path,
                "file_path": str(file_path.relative_to(self.project_root)),
                "type": self._get_app_route_type(file_path)
            })

        return routes

    def _extract_pages_routes(self) -> List[Dict[str, Any]]:
        """
        Extract routes from /pages directory (Pages Router).

        Returns:
            List of route metadata dicts
        """
        routes = []
        pages_dir = self.project_root / "pages"

        if not pages_dir.exists():
            return routes

        for file_path in pages_dir.rglob('*'):
            if not file_path.is_file():
                continue

            if file_path.suffix not in ['.js', '.jsx', '.ts', '.tsx']:
                continue

            # Extract route path from file path
            route_path = self._get_pages_route_path(file_path, pages_dir)

            routes.append({
                "path": route_path,
                "file_path": str(file_path.relative_to(self.project_root)),
                "type": "page"
            })

        return routes

    def _extract_api_routes(self) -> List[Dict[str, Any]]:
        """
        Extract API routes from /pages/api directory.

        Returns:
            List of API route metadata dicts
        """
        routes = []
        api_dir = self.project_root / "pages" / "api"

        if not api_dir.exists():
            return routes

        for file_path in api_dir.rglob('*'):
            if not file_path.is_file():
                continue

            if file_path.suffix not in ['.js', '.jsx', '.ts', '.tsx']:
                continue

            # Extract route path from file path
            route_path = self._get_pages_route_path(file_path, api_dir)

            routes.append({
                "path": f"/api{route_path}",
                "file_path": str(file_path.relative_to(self.project_root)),
                "type": "api"
            })

        return routes

    def _get_app_route_path(self, file_path: Path, app_dir: Path) -> str:
        """
        Convert file path to App Router route path.

        Args:
            file_path: Absolute path to route file
            app_dir: App directory path

        Returns:
            Route path (e.g., '/dashboard/[id]')
        """
        relative = file_path.relative_to(app_dir)

        # Remove extension and convert to route
        parts = list(relative.parts[:-1])  # Remove filename

        # Handle special files
        filename = relative.stem
        if filename == 'page':
            pass  # Regular page, use parent dir as route
        elif filename == 'layout':
            parts.append('_layout')
        elif filename == 'loading':
            parts.append('_loading')
        elif filename == 'error':
            parts.append('_error')
        elif filename == 'not-found':
            parts.append('_not-found')
        else:
            parts.append(filename)

        # Convert to route path
        if not parts or parts[0] == '':
            return '/'

        route = '/' + '/'.join(parts)
        return route

    def _get_pages_route_path(self, file_path: Path, pages_dir: Path) -> str:
        """
        Convert file path to Pages Router route path.

        Args:
            file_path: Absolute path to route file
            pages_dir: Pages directory path

        Returns:
            Route path (e.g., '/blog/[slug]')
        """
        relative = file_path.relative_to(pages_dir)

        # Remove extension and convert to route
        parts = list(relative.parts[:-1])  # Remove filename
        filename = relative.stem

        # Handle index file
        if filename == 'index':
            pass  # Route is determined by directory
        else:
            parts.append(filename)

        # Convert to route path
        if not parts or parts[0] == '':
            return '/'

        route = '/' + '/'.join(parts)
        return route

    def _get_app_route_type(self, file_path: Path) -> str:
        """
        Determine the type of App Router file.

        Args:
            file_path: Path to the file

        Returns:
            Route type string
        """
        filename = file_path.stem

        if filename == 'page':
            return 'page'
        elif filename == 'layout':
            return 'layout'
        elif filename == 'loading':
            return 'loading'
        elif filename == 'error':
            return 'error'
        elif filename == 'not-found':
            return 'not-found'
        elif filename == 'template':
            return 'template'
        else:
            return 'component'

    def get_framework_hints(self) -> Dict[str, Any]:
        """
        Get framework-specific hints for concept extraction.

        Returns:
            Dict with framework metadata
        """
        hints = {
            "framework": None,
            "router_type": None,
            "routes": []
        }

        if not self.is_nextjs_project():
            return hints

        hints["framework"] = "nextjs"
        hints["router_type"] = self.get_router_type()
        hints["routes"] = self.extract_routes()

        return hints
