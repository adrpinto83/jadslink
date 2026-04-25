#!/usr/bin/env python3
"""
JADSlink OpenWrt Setup Wizard
Guía interactiva para configurar un nodo OpenWrt
"""

import sys
import os
import subprocess
import json
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

class SetupWizard:
    def __init__(self):
        self.agent_dir = Path(__file__).parent
        self.state = {
            'validated': False,
            'openwrt_host': None,
            'openwrt_user': 'root',
            'openwrt_port': 22,
            'credentials': {},
            'deployed': False,
            'tested': False,
        }

    def clear_screen(self):
        """Limpia la pantalla"""
        os.system('clear' if os.name != 'nt' else 'cls')

    def print_header(self, text: str):
        """Imprime encabezado"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

    def print_section(self, text: str, step: Optional[int] = None):
        """Imprime sección"""
        prefix = f"[{step}] " if step else ""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{prefix}{text}{Colors.END}")
        print(f"{Colors.DIM}{'-'*70}{Colors.END}")

    def print_ok(self, text: str):
        """Imprime OK"""
        print(f"{Colors.GREEN}✓ {text}{Colors.END}")

    def print_error(self, text: str):
        """Imprime error"""
        print(f"{Colors.RED}✗ {text}{Colors.END}")

    def print_warning(self, text: str):
        """Imprime advertencia"""
        print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

    def print_info(self, text: str):
        """Imprime info"""
        print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

    def print_input(self, prompt: str, default: Optional[str] = None) -> str:
        """Obtiene input del usuario"""
        if default:
            prompt_text = f"{Colors.BOLD}{prompt} [{Colors.CYAN}{default}{Colors.BOLD}]{Colors.END}: "
        else:
            prompt_text = f"{Colors.BOLD}{prompt}{Colors.END}: "

        user_input = input(prompt_text).strip()
        return user_input if user_input else (default or "")

    def print_menu(self, title: str, options: dict) -> str:
        """Menú interactivo"""
        print(f"\n{Colors.BOLD}{title}{Colors.END}")
        for key, value in options.items():
            print(f"  {Colors.CYAN}{key}{Colors.END}) {value}")

        choice = input(f"\n{Colors.BOLD}Selecciona una opción{Colors.END}: ").strip()
        return choice

    def run_command(self, cmd: str, check: bool = True) -> Tuple[bool, str]:
        """Ejecuta comando y retorna (success, output)"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            if check and result.returncode != 0:
                return False, result.stderr or result.stdout
            return True, result.stdout
        except Exception as e:
            return False, str(e)

    def step_welcome(self):
        """Bienvenida y explicación"""
        self.clear_screen()
        self.print_header("JADSlink OpenWrt Setup Wizard")

        print(f"""
{Colors.BOLD}Este asistente te guiará para configurar un dispositivo OpenWrt{Colors.END}
{Colors.BOLD}como nodo JADSlink.{Colors.END}

{Colors.CYAN}¿Qué vamos a hacer?{Colors.END}

  1. {Colors.BOLD}Validar{Colors.END} que todo está listo en tu máquina
  2. {Colors.BOLD}Conectar{Colors.END} a tu dispositivo OpenWrt vía SSH
  3. {Colors.BOLD}Instalar{Colors.END} el agente JADSlink
  4. {Colors.BOLD}Probar{Colors.END} que todo funcione
  5. {Colors.BOLD}Ver{Colors.END} instrucciones de testing

{Colors.YELLOW}Requisitos:{Colors.END}
  • Dashboard JADSlink con nodo y planes creados
  • Dispositivo OpenWrt en la red local
  • SSH habilitado en OpenWrt
  • Credenciales del nodo (NODE_ID, API_KEY)

{Colors.GREEN}¡Comenzamos!{Colors.END}
""")

        input(f"{Colors.BOLD}Presiona ENTER para continuar...{Colors.END}")

    def step_validate_setup(self):
        """Valida que todo está listo localmente"""
        self.print_section("PASO 1: Validar Setup Local", step=1)

        print("Verificando que el script de validación existe...")

        validate_script = self.agent_dir / "validate-setup.py"

        if not validate_script.exists():
            self.print_error("validate-setup.py no encontrado")
            return False

        self.print_ok("Script de validación encontrado")

        print("\nEjecutando validación...")
        success, output = self.run_command(f"python3 {validate_script}", check=False)

        if "✓ Todo está listo" in output:
            self.print_ok("Validación completada exitosamente")
            self.state['validated'] = True
            return True
        else:
            self.print_error("Validación falló. Ver detalles arriba.")
            return False

    def step_openwrt_credentials(self):
        """Obtiene credenciales de OpenWrt"""
        self.print_section("PASO 2: Conectar a OpenWrt", step=2)

        self.print_info("Necesitamos información para conectar a tu OpenWrt")

        self.state['openwrt_host'] = self.print_input(
            "IP/Hostname de OpenWrt",
            default="10.0.0.1"
        )

        self.state['openwrt_user'] = self.print_input(
            "Usuario SSH",
            default="root"
        )

        self.state['openwrt_port'] = int(self.print_input(
            "Puerto SSH",
            default="22"
        ))

        print("\nVerificando conectividad SSH...")

        cmd = f"ssh -p {self.state['openwrt_port']} {self.state['openwrt_user']}@{self.state['openwrt_host']} -o ConnectTimeout=5 'exit 0' 2>/dev/null"
        success, _ = self.run_command(cmd, check=False)

        if success:
            self.print_ok(f"Conectado a {self.state['openwrt_host']}")
            return True
        else:
            self.print_error(f"No se puede conectar a {self.state['openwrt_host']}")
            self.print_info("Soluciones:")
            print("  1. Verifica que OpenWrt está encendido")
            print("  2. Verifica la IP con: ping 10.0.0.1")
            print("  3. Habilita SSH en OpenWrt (LuCI)")
            return False

    def step_node_credentials(self):
        """Obtiene credenciales del nodo"""
        self.print_section("PASO 3: Credenciales del Nodo", step=3)

        self.print_info("Obtén estas credenciales del Dashboard JADSlink")
        self.print_info("Dashboard → Nodos → Tu Nodo")

        node_id = self.print_input("NODE_ID (UUID)")
        api_key = self.print_input("API_KEY (sk_live_...)")
        server_url = self.print_input(
            "SERVER_URL",
            default="http://192.168.0.X:8000"
        )

        # Validar formato
        if not self._validate_uuid(node_id):
            self.print_error("NODE_ID inválido")
            return False

        if not api_key.startswith("sk_live_"):
            self.print_error("API_KEY debe comenzar con 'sk_live_'")
            return False

        self.state['credentials'] = {
            'NODE_ID': node_id,
            'API_KEY': api_key,
            'SERVER_URL': server_url,
        }

        self.print_ok("Credenciales validadas")
        return True

    def _validate_uuid(self, uuid_string: str) -> bool:
        """Valida formato UUID"""
        import re
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(pattern, uuid_string.lower()))

    def step_review_and_confirm(self):
        """Revisa y confirma la configuración"""
        self.print_section("PASO 4: Revisar Configuración", step=4)

        print(f"{Colors.BOLD}OpenWrt:{Colors.END}")
        print(f"  Host: {self.state['openwrt_host']}")
        print(f"  Usuario: {self.state['openwrt_user']}")
        print(f"  Puerto: {self.state['openwrt_port']}")

        print(f"\n{Colors.BOLD}Nodo JADSlink:{Colors.END}")
        print(f"  NODE_ID: {self.state['credentials']['NODE_ID'][:8]}...")
        print(f"  API_KEY: {self.state['credentials']['API_KEY'][:15]}...")
        print(f"  SERVER_URL: {self.state['credentials']['SERVER_URL']}")

        choice = self.print_menu(
            "¿Todo correcto?",
            {"s": "Sí, continuar", "n": "No, editar"}
        )

        return choice.lower() == "s"

    def step_deploy_agent(self):
        """Despliega el agente a OpenWrt"""
        self.print_section("PASO 5: Desplegar Agente", step=5)

        print("Este paso:")
        print("  1. Transferirá archivos del agente vía SCP")
        print("  2. Configurará el archivo .env con tus credenciales")
        print("  3. Creará el init script")
        print("  4. Verificará la instalación")

        choice = self.print_menu(
            "¿Proceder con el deploy?",
            {"s": "Sí, desplegar", "n": "No, cancelar"}
        )

        if choice.lower() != "s":
            return False

        print("\n1. Transfiriendo archivos...")

        deploy_script = self.agent_dir / "deploy-to-openwrt.sh"
        cmd = f"bash {deploy_script} {self.state['openwrt_host']} {self.state['openwrt_user']} {self.state['openwrt_port']}"
        success, output = self.run_command(cmd, check=False)

        if not success:
            self.print_error("Error en deploy:")
            print(output)
            return False

        self.print_ok("Archivos transferidos")

        print("\n2. Configurando .env...")

        env_content = f"""# JADSlink Node Configuration
# Generated by setup-wizard.py on {datetime.now().isoformat()}

NODE_ID={self.state['credentials']['NODE_ID']}
API_KEY={self.state['credentials']['API_KEY']}
SERVER_URL={self.state['credentials']['SERVER_URL']}

ROUTER_IP=10.0.0.1
PORTAL_PORT=80
PORTAL_HOST=0.0.0.0

HEARTBEAT_INTERVAL=30
SYNC_INTERVAL=300
EXPIRE_INTERVAL=60

CACHE_DIR=/opt/jadslink/.cache
"""

        # Crear .env remoto
        cmd = f"ssh -p {self.state['openwrt_port']} {self.state['openwrt_user']}@{self.state['openwrt_host']} 'cat > /opt/jadslink/.env << EOF\n{env_content}\nEOF\nchmod 600 /opt/jadslink/.env'"
        success, _ = self.run_command(cmd, check=False)

        if success:
            self.print_ok(".env configurado")
        else:
            self.print_error("Error configurando .env")
            return False

        print("\n3. Verificando instalación...")

        test_script = self.agent_dir / "test-openwrt.sh"
        cmd = f"bash {test_script} {self.state['openwrt_host']} {self.state['openwrt_user']} {self.state['openwrt_port']}"
        success, output = self.run_command(cmd, check=False)

        if success:
            print(output)
            self.print_ok("Instalación verificada")
            self.state['deployed'] = True
            return True
        else:
            self.print_error("Error en verificación:")
            print(output)
            return False

    def step_start_agent(self):
        """Inicia el agente"""
        self.print_section("PASO 6: Iniciar Agente", step=6)

        choice = self.print_menu(
            "¿Iniciar el servicio JADSlink?",
            {"s": "Sí, iniciar", "n": "No, luego"}
        )

        if choice.lower() != "s":
            return True

        print("Iniciando servicio...")

        cmd = f"ssh -p {self.state['openwrt_port']} {self.state['openwrt_user']}@{self.state['openwrt_host']} '/etc/init.d/jadslink start'"
        success, output = self.run_command(cmd, check=False)

        if success:
            self.print_ok("Servicio iniciado")

            print("\nEsperando a que el nodo se registre (30 segundos)...")
            import time
            for i in range(30, 0, -1):
                print(f"  {i}...", end='\r')
                time.sleep(1)

            print("  ✓")
            self.state['tested'] = True
            return True
        else:
            self.print_error("Error iniciando servicio:")
            print(output)
            return False

    def step_final_instructions(self):
        """Instrucciones finales"""
        self.clear_screen()
        self.print_header("✓ ¡Setup Completado!")

        print(f"""
{Colors.GREEN}Tu nodo OpenWrt ha sido configurado exitosamente.{Colors.END}

{Colors.BOLD}Próximos pasos:{Colors.END}

1. {Colors.BOLD}Verificar en Dashboard:{Colors.END}
   • Ve a http://localhost:5173/dashboard/nodes
   • Tu nodo "{self.state['openwrt_host']}" debe aparecer con estado "online"

2. {Colors.BOLD}Generar Tickets:{Colors.END}
   • Dashboard → Tickets → Generar Batch
   • Selecciona tu nodo y plan
   • Descarga el PDF con QR codes

3. {Colors.BOLD}Testing End-to-End:{Colors.END}
   • Conecta un móvil a WiFi "JADSlink-WiFi"
   • Intenta acceder a cualquier sitio web
   • Deberías ver el portal captive
   • Ingresa un código de ticket
   • ¡Deberías tener internet!

{Colors.BOLD}Comandos útiles:{Colors.END}

Ver logs en tiempo real:
  ssh root@{self.state['openwrt_host']} 'logread -f | grep jadslink'

Reiniciar agente:
  ssh root@{self.state['openwrt_host']} '/etc/init.d/jadslink restart'

Ver estado:
  ssh root@{self.state['openwrt_host']} 'ps | grep agent.py'

{Colors.BOLD}Documentación:{Colors.END}
  • Agent README: /agent/README.md
  • API Docs: http://localhost:8000/docs
  • Troubleshooting: CLAUDE.md → Troubleshooting

{Colors.YELLOW}¿Problemas?{Colors.END}
  1. Ver logs: logread -f | grep jadslink
  2. Verificar conectividad: curl http://SERVER_URL/docs
  3. Revisar .env: cat /opt/jadslink/.env
  4. Leer troubleshooting en CLAUDE.md

{Colors.GREEN}¡Listo para operar!{Colors.END}
""")

        input(f"{Colors.BOLD}Presiona ENTER para terminar...{Colors.END}")

    def run(self):
        """Ejecuta el wizard"""
        try:
            # Bienvenida
            self.step_welcome()

            # Paso 1: Validar setup local
            if not self.step_validate_setup():
                self.print_error("Setup local no válido. Por favor revisa los errores arriba.")
                sys.exit(1)

            # Paso 2: Credenciales OpenWrt
            while not self.step_openwrt_credentials():
                print("\n" + Colors.YELLOW + "Intenta de nuevo..." + Colors.END)

            # Paso 3: Credenciales del nodo
            while not self.step_node_credentials():
                print("\n" + Colors.YELLOW + "Intenta de nuevo..." + Colors.END)

            # Paso 4: Revisar y confirmar
            while not self.step_review_and_confirm():
                self.step_openwrt_credentials()
                self.step_node_credentials()

            # Paso 5: Deploy
            if not self.step_deploy_agent():
                self.print_error("Deploy cancelado")
                sys.exit(1)

            # Paso 6: Iniciar agente
            self.step_start_agent()

            # Paso 7: Instrucciones finales
            self.step_final_instructions()

        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Setup cancelado por el usuario{Colors.END}")
            sys.exit(0)
        except Exception as e:
            print(f"\n{Colors.RED}Error: {e}{Colors.END}")
            sys.exit(1)

def main():
    wizard = SetupWizard()
    wizard.run()

if __name__ == '__main__':
    main()
