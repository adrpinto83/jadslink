#!/usr/bin/env python3
"""
JADSlink OpenWrt Setup Validator
Verifica que todo está listo antes de configurar el nodo en OpenWrt
"""

import sys
import os
import json
from pathlib import Path
from typing import Tuple, Dict, List
from datetime import datetime

try:
    import requests
except ImportError:
    print("❌ ERROR: requests no está instalado")
    print("   Instala con: pip3 install requests")
    sys.exit(1)

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

class Validator:
    def __init__(self):
        self.env_file = Path(__file__).parent / '.env'
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.config: Dict = {}

    def print_header(self, text: str):
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

    def print_section(self, text: str):
        print(f"\n{Colors.BOLD}{text}{Colors.END}")
        print("-" * 40)

    def print_ok(self, text: str):
        print(f"{Colors.GREEN}✓ {text}{Colors.END}")

    def print_error(self, text: str):
        print(f"{Colors.RED}✗ {text}{Colors.END}")
        self.errors.append(text)

    def print_warning(self, text: str):
        print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")
        self.warnings.append(text)

    def print_info(self, text: str):
        print(f"{Colors.BLUE}ℹ {text}{Colors.END}")
        self.info.append(text)

    def load_env(self) -> bool:
        """Carga variables de .env"""
        self.print_section("1. Verificando archivo .env")

        if not self.env_file.exists():
            self.print_error(f".env no encontrado en {self.env_file}")
            self.print_info(f"Crea uno basado en .env.example:")
            print(f"   cp {self.env_file.parent / '.env.example'} {self.env_file}")
            print(f"   # Editar {self.env_file} con tus credenciales")
            return False

        self.print_ok(".env encontrado")

        try:
            with open(self.env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            self.config[key] = value
            self.print_ok(f"Cargadas {len(self.config)} variables")
            return True
        except Exception as e:
            self.print_error(f"Error leyendo .env: {e}")
            return False

    def validate_credentials(self) -> bool:
        """Valida que NODE_ID y API_KEY existan"""
        self.print_section("2. Validando credenciales del nodo")

        node_id = self.config.get('NODE_ID', '')
        api_key = self.config.get('API_KEY', '')

        # Validar NODE_ID
        if not node_id or node_id == '00000000-0000-0000-0000-000000000000':
            self.print_error("NODE_ID no configurado o es placeholder")
            self.print_info("Obten NODE_ID del dashboard: Dashboard → Nodos → Crear Nodo")
            return False
        self.print_ok(f"NODE_ID: {node_id[:8]}...")

        # Validar API_KEY
        if not api_key or api_key == 'generate-from-dashboard':
            self.print_error("API_KEY no configurado o es placeholder")
            self.print_info("Obtén API_KEY del mismo sitio donde obtuviste NODE_ID")
            return False
        if not api_key.startswith('sk_live_'):
            self.print_warning("API_KEY no comienza con 'sk_live_' (¿es válida?)")
        self.print_ok(f"API_KEY: {api_key[:15]}...")

        return True

    def validate_server_url(self) -> bool:
        """Valida que SERVER_URL sea accesible"""
        self.print_section("3. Validando conexión al servidor JADSlink")

        server_url = self.config.get('SERVER_URL', '').rstrip('/')
        if not server_url:
            self.print_error("SERVER_URL no configurado")
            return False

        self.print_info(f"Intentando conectar a: {server_url}")

        try:
            response = requests.get(
                f"{server_url}/docs",
                timeout=5
            )
            if response.status_code == 200:
                self.print_ok(f"✓ Servidor accesible ({response.status_code})")
                return True
            else:
                self.print_warning(f"Servidor respondió con status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            self.print_error(f"No se puede conectar a {server_url}")
            self.print_info("Verifica que el servidor esté corriendo:")
            print("   docker compose logs api")
            return False
        except requests.exceptions.Timeout:
            self.print_error(f"Timeout al conectar a {server_url}")
            return False
        except Exception as e:
            self.print_error(f"Error: {e}")
            return False

    def validate_node_exists(self) -> bool:
        """Valida que el nodo existe en el servidor"""
        self.print_section("4. Validando nodo en el servidor")

        server_url = self.config.get('SERVER_URL', '').rstrip('/')
        node_id = self.config.get('NODE_ID', '')
        api_key = self.config.get('API_KEY', '')

        if not all([server_url, node_id, api_key]):
            self.print_error("Faltan credenciales para validar nodo")
            return False

        try:
            response = requests.get(
                f"{server_url}/api/v1/nodes/{node_id}",
                headers={'Authorization': f'Bearer {api_key}'},
                timeout=5
            )

            if response.status_code == 200:
                node = response.json()
                self.print_ok(f"✓ Nodo encontrado: {node.get('name', 'N/A')}")
                self.print_info(f"  Serial: {node.get('serial_number', 'N/A')}")
                self.print_info(f"  Status: {node.get('status', 'N/A')}")
                return True
            elif response.status_code == 401:
                self.print_error("API_KEY inválido (401 Unauthorized)")
                return False
            elif response.status_code == 404:
                self.print_error("Nodo no encontrado (404)")
                self.print_info("Verifica que el NODE_ID sea correcto")
                return False
            else:
                self.print_error(f"Error {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Error validando nodo: {e}")
            return False

    def check_python_version(self) -> bool:
        """Verifica versión de Python"""
        self.print_section("5. Verificando Python")

        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            self.print_error(f"Python 3.9+ requerido (tienes {version.major}.{version.minor})")
            return False
        self.print_ok(f"Python {version.major}.{version.minor}.{version.micro}")
        return True

    def check_dependencies(self) -> bool:
        """Verifica dependencias Python"""
        self.print_section("6. Verificando dependencias Python")

        required = ['requests', 'schedule', 'sqlite3']
        optional = ['dotenv']
        missing = []

        for pkg in required:
            try:
                if pkg == 'sqlite3':
                    import sqlite3
                else:
                    __import__(pkg)
                self.print_ok(f"{pkg}")
            except ImportError:
                self.print_error(f"{pkg} - NO ENCONTRADO")
                missing.append(pkg)

        for pkg in optional:
            try:
                __import__(pkg)
                self.print_ok(f"{pkg} (optional)")
            except ImportError:
                self.print_warning(f"{pkg} no instalado (opcional)")

        if missing:
            print(f"\nInstala con: pip3 install {' '.join(missing)}")
            return False
        return True

    def check_network_config(self) -> bool:
        """Valida configuración de red"""
        self.print_section("7. Validando configuración de red")

        router_ip = self.config.get('ROUTER_IP', '')
        portal_port = self.config.get('PORTAL_PORT', '')

        if not router_ip:
            self.print_warning("ROUTER_IP no configurado (se autodetectará en OpenWrt)")
        else:
            self.print_ok(f"ROUTER_IP: {router_ip}")

        if not portal_port:
            self.print_warning("PORTAL_PORT no configurado (usará 80)")
        elif portal_port == '80':
            self.print_ok(f"PORTAL_PORT: {portal_port} (producción)")
        elif portal_port == '8080':
            self.print_warning(f"PORTAL_PORT: {portal_port} (desarrollo)")
        else:
            self.print_warning(f"PORTAL_PORT: {portal_port} (inusual)")

        return True

    def run_all_checks(self) -> bool:
        """Ejecuta todas las validaciones"""
        self.print_header("JADSlink Agent Setup Validator")

        checks = [
            ("Cargando .env", self.load_env),
            ("Validando credenciales", self.validate_credentials),
            ("Validando servidor", self.validate_server_url),
            ("Validando nodo", self.validate_node_exists),
            ("Verificando Python", self.check_python_version),
            ("Verificando dependencias", self.check_dependencies),
            ("Validando red", self.check_network_config),
        ]

        results = []
        for name, check_func in checks:
            try:
                result = check_func()
                results.append((name, result))
            except Exception as e:
                self.print_error(f"Error en {name}: {e}")
                results.append((name, False))

        # Resumen
        self.print_header("RESUMEN")

        passed = sum(1 for _, r in results if r)
        total = len(results)

        print(f"Validaciones pasadas: {Colors.GREEN}{passed}/{total}{Colors.END}")

        if self.warnings:
            print(f"\n{Colors.YELLOW}⚠ Advertencias ({len(self.warnings)}):{Colors.END}")
            for w in self.warnings:
                print(f"  • {w}")

        if self.errors:
            print(f"\n{Colors.RED}✗ Errores ({len(self.errors)}):{Colors.END}")
            for e in self.errors:
                print(f"  • {e}")
            return False

        print(f"\n{Colors.GREEN}✓ Todo está listo para configurar OpenWrt{Colors.END}")
        print("\nSiguientes pasos:")
        print("1. Conectar a OpenWrt vía SSH")
        print("   ssh root@192.168.0.209  (o la IP de tu dispositivo)")
        print("\n2. Ejecutar script de instalación")
        print("   bash openwrt-setup.sh")
        print("\n3. Copiar las credenciales cuando se solicite:")
        print(f"   NODE_ID: {self.config.get('NODE_ID', 'N/A')}")
        print(f"   API_KEY: {self.config.get('API_KEY', 'N/A')}")
        print(f"   SERVER_URL: {self.config.get('SERVER_URL', 'N/A')}")

        return True

def main():
    validator = Validator()
    success = validator.run_all_checks()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
