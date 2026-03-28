# DBX-V2 Desktop

Este diretório concentra a camada desktop da aplicação `.exe`.

## Estrutura atual

- `main_window.py`: janela principal e composição da interface PyQt5
- `history_dialog.py`: diálogo de histórico de projetos
- `nesting_dialog.py`: diálogo de cálculo de aproveitamento
- `processing.py`: worker/thread de geração de PDF e DXF

## Observações

- Os módulos compartilhados com a API e outras camadas continuam temporariamente na raiz do projeto.
- Os arquivos `main.py`, `history_dialog.py`, `nesting_dialog.py` e `processing.py` na raiz agora são wrappers de compatibilidade.
- O objetivo desta fase foi separar fisicamente a aplicação desktop da versão web sem quebrar o fluxo atual.
