# Progress Bubble — Codex, Claude Code e Antigravity

Uma bolinha flutuante para acompanhar o trabalho do Codex, Claude Code e Google Antigravity, com anel de progresso, cartão de status e página HTML local. Um único pacote de skill e os mesmos scripts atendem aos três agentes.

![Ilustração do cartão e da bolinha](assets/preview.svg)

## O que faz

- Orienta o agente a abrir o acompanhamento em demandas estimadas acima de **30 segundos**, ou quando a execução ultrapassar esse tempo.
- Mostra percentual estimado, status, mensagem curta e horário da atualização.
- No Windows, mantém uma bolinha por cima das janelas: clique para expandir, arraste para mover e use × para fechar.
- Gera HTML independente, sem servidor, conta ou bibliotecas externas.
- Usa cores diferentes para conclusão, falha e espera.

O progresso é estimado e atualizado pelo agente. A skill não intercepta todas as execuções, não mede automaticamente o trabalho e não garante intervalos exatos durante chamadas bloqueantes. A bolinha lê os dados salvos a cada 2 segundos; o agente busca atualizá-los aproximadamente a cada 30 segundos.

## Requisitos

| Recurso | Requisitos |
| --- | --- |
| HTML e JSON | Python 3.10+; navegador para visualizar o HTML |
| Bolinha flutuante | Windows, sessão gráfica, Python com Tkinter e `pythonw.exe` |
| Ativação por demanda | Codex, Claude Code local ou Antigravity com suporte a skills e permissão para gravar arquivos/executar Python |

A janela usa APIs do Windows. Em Linux, macOS e ambientes sem desktop, use o acompanhamento HTML. Não há dependências de pip. Confira o Tkinter no Windows com `python -m tkinter` (abre uma janela de teste).

## Instalar nos três agentes

Clone ou baixe este repositório. Na raiz, execute o instalador com Python 3.10+:

```powershell
python install.py --agent codex
python install.py --agent claude
python install.py --agent antigravity
```

Ou instale para os três de uma vez:

```powershell
python install.py --agent all
```

Por padrão a instalação é pessoal/global. Para instalar somente em um projeto:

```powershell
python install.py --agent all --scope project --project-root "C:/caminho/do/projeto"
```

Em macOS/Linux, substitua o caminho pelo do projeto e use `python3` se necessário. O HTML funciona nesses sistemas; a bolinha requer Windows nativo. Execute os comandos no computador onde o agente roda. O script não instala Python nem altera permissões.

| Agente | Pasta pessoal/global | Pasta dentro do projeto | Invocação explícita |
| --- | --- | --- | --- |
| Codex | `~/.agents/skills/` | `.agents/skills/` | `$acompanhar-demandas-longas` |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` | `/acompanhar-demandas-longas` |
| Antigravity App/IDE/CLI | `~/.gemini/config/skills/` | `.agents/skills/` | `/acompanhar-demandas-longas` |

O instalador copia a pasta inteira, sem links simbólicos. No escopo de projeto, Codex e Antigravity compartilham a mesma instalação. Use `--dry-run` para apenas mostrar os destinos. Uma instalação existente causa erro antes de copiar qualquer arquivo; para atualizar, faça backup e mova a pasta anterior antes de repetir. Não instale cópias pessoais e de projeto desnecessariamente.

Recarregue as skills ou inicie uma nova sessão do agente após instalar. No Antigravity CLI, também pode usar `/skills reload`. Em versões antigas do Antigravity, consulte a documentação da versão: os caminhos legados podem diferir. No Codex com instalação antiga em `~/.codex/skills/`, prefira atualizar a cópia existente a criar uma duplicata.

### Instalação pelo Codex

Envie este pedido ao Codex:

> Use $skill-installer para instalar https://github.com/EvandroSilvaPinto/codex-progress-bubble/tree/main/skills/acompanhar-demandas-longas

Para instalação manual em qualquer agente, copie **a pasta inteira** `skills/acompanhar-demandas-longas` para o destino da tabela. O `SKILL.md` usa campos comuns; `agents/openai.yaml` é metadado opcional do Codex e não é necessário para os outros agentes.

Referências oficiais: [Codex](https://learn.chatgpt.com/docs/build-skills), [Claude Code](https://code.claude.com/docs/en/skills) e [Antigravity](https://antigravity.google/docs/skills). Caminhos conferidos em 13/11/2026.

## Usar

Use a invocação correspondente na tabela ou deixe o agente selecionar a skill conforme a demanda. Para reforçar a preferência em todos os projetos, inclua nas suas instruções permanentes (por exemplo, `AGENTS.md` no Codex, `CLAUDE.md` no Claude Code ou regras do Antigravity):

> Use a skill acompanhar-demandas-longas nas demandas estimadas acima de 30 segundos e nas execuções que ultrapassarem esse tempo.

O limite é uma instrução para o agente, e não um cronômetro do sistema. Para personalizar, altere o limite no `SKILL.md` e na descrição em `agents/openai.yaml`.

A skill resolve os scripts a partir da própria pasta instalada, sem caminhos pessoais fixos. No Claude Code, `${CLAUDE_SKILL_DIR}` também pode identificar essa pasta. Não é preciso editar os scripts para trocar de agente. No terminal, use `python`, `python3` ou `py -3`, conforme seu ambiente.

### Demonstração manual

Na raiz deste repositório, em PowerShell:

```powershell
python skills/acompanhar-demandas-longas/scripts/status.py --output outputs/demo.html --title "Preparando relatório" --percent 15 --message "Trabalho iniciado" --open
```

Atualize o mesmo arquivo sem reabrir a janela:

```powershell
python skills/acompanhar-demandas-longas/scripts/status.py --output outputs/demo.html --title "Preparando relatório" --percent 65 --message "Revisando o conteúdo"
```

Finalize:

```powershell
python skills/acompanhar-demandas-longas/scripts/status.py --output outputs/demo.html --title "Preparando relatório" --percent 100 --status "Concluído" --message "Relatório entregue e verificado"
```

Omita `--open` para gerar apenas HTML/JSON. Abra o HTML no navegador; enquanto a demanda estiver ativa ele recarrega a cada 20 segundos. Visualizadores incorporados podem exigir recarga manual.

Estados aceitos: `Em andamento`, `Aguardando informação`, `Concluído`, `Interrompido`, `Falha`. Somente `Concluído` aceita 100%. Em falha, mantenha o percentual alcançado. O horário usa o fuso local do computador.

## Privacidade e limitações

Os scripts gravam os dados no caminho escolhido. Não enviam telemetria nem abrem portas. O botão de detalhes abre o HTML no navegador padrão. Evite colocar credenciais ou informações sensíveis no título e na mensagem e não publique arquivos de acompanhamento reais.

Cada demanda deve usar um nome de arquivo diferente. Uma segunda abertura para o mesmo JSON não duplica a janela. Fechar a bolinha não cancela a demanda. Não há inicialização automática com o Windows nem execução de trabalho após o encerramento do agente. Textos extensos aparecem resumidos no cartão; o HTML preserva o conteúdo completo.

Esta integração com Claude é para **Claude Code local**, não uma extensão do chat web Claude ou uma instalação sincronizada no Cowork. Em WSL, contêineres e agentes remotos, o HTML é a alternativa; rodar o script num ambiente remoto não cria uma janela no seu desktop. As permissões de ferramentas de cada agente continuam valendo.

Se a bolinha não aparecer, confirme os requisitos e execute `python skills/acompanhar-demandas-longas/scripts/bubble.py outputs/demo.json` para ver o erro no terminal. Políticas ou permissões do ambiente podem impedir a janela.

## Desenvolvimento

```powershell
python -m unittest discover -s tests -v
```

Os testes cobrem o instalador por agente, instalação conjunta no projeto, execução da skill instalada em outro caminho, preservação de instalações existentes, interface de linha de comando, caracteres especiais, estados e conclusão. O CI executa em Windows/Linux com Python 3.10/3.13.

**Limite da validação:** os caminhos de descoberta e as invocações seguem as documentações oficiais. Os testes verificam os arquivos instalados e os scripts; não comprovam que cada modelo selecionará a skill automaticamente. A janela foi inspecionada manualmente em Windows com Python 3.13. A seleção automática deve ser conferida numa sessão de cada agente; a invocação explícita é a forma de teste inicial.

Contribuições por issues e pull requests são bem-vindas. Para bugs, informe sistema operacional, versão do Python, comando utilizado e resultado esperado, sem anexar dados privados.

## Licença

[MIT](LICENSE). Projeto independente, sem afiliação oficial com OpenAI, Anthropic ou Google.
