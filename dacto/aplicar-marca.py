"""Aplica a identidade "Dacto Suporte" ao código-fonte do RustDesk.

Uso (a partir de C:\\Sistemas\\rustdesk):
    py -I branding/aplicar-marca.py --src rustdesk --host suporte.dacto.com.br \
        --key <chave_publica> [--logo branding/logo.png] [--icone branding/icone.png]

- Idempotente para nome/servidor/chave: pode rodar mais de uma vez (substituições por regex).
- --logo  : logo horizontal (vai para a tela principal, máx. 300x60 exibido).
- --icone : símbolo quadrado (ícone do .exe, bandeja e atalhos). Se omitido, usa --logo
            centralizada num quadrado transparente.
Testado contra RustDesk 1.5.3. Em outra versão, o script avisa se algum trecho não for encontrado.
"""
import argparse
import re
import sys
from pathlib import Path

NOME_PADRAO = "Dacto Suporte"
EMPRESA = "Dacto Contabilidade"

erros = []


def substituir(arquivo: Path, padrao: str, novo: str, descricao: str, dotall: bool = False):
    # newline="" preserva CRLF/LF originais (evita diff no arquivo inteiro)
    with open(arquivo, encoding="utf-8", newline="") as f:
        texto = f.read()
    flags = re.MULTILINE | (re.DOTALL if dotall else 0)
    novo_texto, n = re.subn(padrao, lambda _m: novo, texto, count=1, flags=flags)
    if n == 0:
        erros.append(f"[NÃO ENCONTRADO] {descricao} em {arquivo}")
        return
    if novo_texto != texto:
        arquivo.write_bytes(novo_texto.encode("utf-8"))
    print(f"[ok] {descricao}")


def aplicar_config(src: Path, nome: str, host: str, key: str, travar: bool):
    cfg = src / "libs/hbb_common/src/config.rs"
    substituir(cfg, r'pub static ref APP_NAME: RwLock<String> = RwLock::new\(".*?"\.to_owned\(\)\);',
               f'pub static ref APP_NAME: RwLock<String> = RwLock::new("{nome}".to_owned());', "APP_NAME")
    substituir(cfg, r'pub static ref PROD_RENDEZVOUS_SERVER: RwLock<String> = RwLock::new\(".*?"\.to_owned\(\)\);',
               f'pub static ref PROD_RENDEZVOUS_SERVER: RwLock<String> = RwLock::new("{host}".to_owned());',
               "PROD_RENDEZVOUS_SERVER (evita cair na API pública admin.rustdesk.com)")
    substituir(cfg, r'pub const RENDEZVOUS_SERVERS: &\[&str\] = &\[.*?\];',
               f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{host}"];', "RENDEZVOUS_SERVERS")
    substituir(cfg, r'pub const RS_PUB_KEY: &str = ".*?";',
               f'pub const RS_PUB_KEY: &str = "{key}";', "RS_PUB_KEY")
    if travar:
        # Servidor e chave fixos: o colaborador não consegue apontar o app para outro servidor.
        mapa = (
            "RwLock::new(HashMap::from([\n"
            f'        ("custom-rendezvous-server".to_owned(), "{host}".to_owned()),\n'
            f'        ("key".to_owned(), "{key}".to_owned()),\n'
            "    ]))"
        )
        substituir(cfg, r'pub static ref OVERWRITE_SETTINGS: RwLock<HashMap<String, String>> = (?:Default::default\(\)|RwLock::new\(HashMap::from\(\[.*?\]\)\));',
                   f"pub static ref OVERWRITE_SETTINGS: RwLock<HashMap<String, String>> = {mapa};",
                   "OVERWRITE_SETTINGS (servidor travado)", dotall=True)


def aplicar_runner_rc(src: Path, nome: str):
    rc = src / "flutter/windows/runner/Runner.rc"
    trocas = {
        "CompanyName": EMPRESA,
        "FileDescription": nome,
        "LegalCopyright": f"{EMPRESA}. Baseado no RustDesk (AGPL-3.0).",
        "ProductName": nome,
    }
    for campo, valor in trocas.items():
        substituir(rc, rf'VALUE "{campo}", ".*?" "\\0"', f'VALUE "{campo}", "{valor}" "\\0"', f"Runner.rc {campo}")


def quadrado(img, lado):
    from PIL import Image
    img = img.convert("RGBA")
    img.thumbnail((lado, lado), Image.LANCZOS)
    tela = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    tela.paste(img, ((lado - img.width) // 2, (lado - img.height) // 2), img)
    return tela


def salvar_logo(origem: Path, destino: Path):
    from PIL import Image
    img = Image.open(origem).convert("RGBA")
    img.thumbnail((600, 120), Image.LANCZOS)  # 2x de 300x60 para telas de alta resolução
    img.save(destino)
    print(f"[ok] {destino.relative_to(destino.parents[2])}")


def aplicar_imagens(src: Path, logo: Path | None, icone: Path | None, logo_escuro: Path | None = None):
    from PIL import Image
    base_icone = Image.open(icone or logo)
    ico256 = quadrado(base_icone, 256)
    tamanhos = [(s, s) for s in (16, 24, 32, 48, 64, 128, 256)]
    for destino in ("res/icon.ico", "res/tray-icon.ico", "flutter/windows/runner/resources/app_icon.ico"):
        ico256.save(src / destino, format="ICO", sizes=tamanhos)
        print(f"[ok] {destino}")
    for destino, lado in (("res/icon.png", 256), ("res/32x32.png", 32), ("res/64x64.png", 64),
                          ("res/128x128.png", 128), ("res/128x128@2x.png", 256),
                          ("flutter/assets/icon.png", 256)):
        quadrado(base_icone, lado).save(src / destino)
        print(f"[ok] {destino}")
    if logo:
        salvar_logo(logo, src / "flutter/assets/logo.png")  # tema claro (e padrão)
    if logo_escuro:
        salvar_logo(logo_escuro, src / "flutter/assets/logo_dark.png")  # tema escuro


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--src", required=True, type=Path, help="pasta do código RustDesk")
    p.add_argument("--host", required=True, help="DNS/IP público do servidor hbbs")
    p.add_argument("--key", required=True, help="conteúdo de id_ed25519.pub")
    p.add_argument("--nome", default=NOME_PADRAO)
    p.add_argument("--logo", type=Path)
    p.add_argument("--icone", type=Path)
    p.add_argument("--logo-escuro", type=Path, help="variante da logo para o tema escuro")
    p.add_argument("--sem-travar", action="store_true", help="permite o usuário trocar o servidor")
    a = p.parse_args()

    if not (a.src / "libs/hbb_common/src/config.rs").exists():
        sys.exit(f"Código RustDesk não encontrado em {a.src}")
    if len(a.key) != 44 or not a.key.endswith("="):
        sys.exit("Chave pública inválida (esperado 44 caracteres base64 terminando em '=').")

    aplicar_config(a.src, a.nome, a.host, a.key, travar=not a.sem_travar)
    aplicar_runner_rc(a.src, a.nome)
    if a.logo or a.icone:
        aplicar_imagens(a.src, a.logo, a.icone, a.logo_escuro)
    else:
        print("[aviso] sem --logo/--icone: ícones continuam os do RustDesk.")

    if erros:
        print("\n".join(erros), file=sys.stderr)
        sys.exit(1)
    print("\nMarca aplicada.")


if __name__ == "__main__":
    main()
