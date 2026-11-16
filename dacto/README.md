# Dacto Suporte

Versão personalizada do [RustDesk](https://github.com/rustdesk/rustdesk) para os colaboradores da
**Dacto Contabilidade** ([dacto.com.br](https://dacto.com.br)), conectada ao servidor próprio da Dacto.

Licença: **AGPL-3.0**, a mesma do RustDesk. Este repositório é o código-fonte correspondente aos
instaladores publicados em *Releases*.

## Como funciona

- Branch `dacto`: código do RustDesk (tag base indicada em `VERSION` do workflow) + esta pasta.
- `dacto/aplicar-marca.py`: aplica nome, servidor, chave, ícones e logo **durante o build**
  (os arquivos originais do RustDesk ficam intactos no repositório, facilitando atualizações).
- `dacto/logo.png` (horizontal) e `dacto/icone.png` (quadrado, opcional): identidade visual.
- `.github/workflows/dacto-windows.yml`: compila o Windows x64 e publica `.exe` e `.msi` em *Releases*.

## Gerar uma versão

1. Variáveis do repositório (*Settings > Secrets and variables > Actions > Variables*):
   `DACTO_HOST` (DNS do servidor) e `DACTO_KEY` (chave **pública** do servidor).
2. *Actions > "Dacto Suporte - build Windows" > Run workflow* (gera pré-release de teste), ou
   criar uma tag `dacto-v1.5.3-1` para uma release oficial.

## Atualizar para uma nova versão do RustDesk

```
git fetch upstream tag <nova-versão> --no-tags
git checkout dacto && git merge <nova-versão>
```
Depois, ajustar `VERSION`/`VCPKG_COMMIT_ID`/`FLUTTER_VERSION` no workflow conforme o
`flutter-build.yml` oficial da nova versão e rodar o build. Se `aplicar-marca.py` acusar
"[NÃO ENCONTRADO]", algum trecho do código mudou e o script precisa ser ajustado.
