# Codex Progress Bubble

Uma bolinha flutuante para acompanhar o trabalho do Codex, com anel de progresso, cartão de status e página HTML local.

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
| Ativação por demanda | Codex com suporte a skills e permissão para gravar arquivos/executar Python |

A janela usa APIs do Windows. Em Linux, macOS e ambientes sem desktop, use o acompanhamento HTML. Não há dependências de pip. Confira o Tkinter no Windows com `python -m tkinter` (abre uma janela de teste).

## Instalar no Codex

Envie este pedido ao Codex:

> Use $skill-installer para instalar https://github.com/EvandroSilvaPinto/codex-progress-bubble/tree/main/skills/acompanhar-demandas-longas

Para instalar a partir de um clone, copie **a pasta inteira** `skills/acompanhar-demandas-longas` para o diretório de skills do usuário, como `~/.agents/skills/`. Para uso apenas em um projeto, copie-a para `.agents/skills/` na raiz desse projeto. Evite instalar a mesma skill em vários lugares. Se ela não aparecer, reinicie o Codex.

Referência: [documentação oficial de skills](https://learn.chatgpt.com/docs/build-skills).

## Usar

Invoque explicitamente com `$acompanhar-demandas-longas` ou deixe o Codex selecioná-la conforme a demanda. Para reforçar a preferência em todos os projetos, inclua nas suas instruções globais:

> Use a skill acompanhar-demandas-longas nas demandas estimadas acima de 30 segundos e nas execuções que ultrapassarem esse tempo.

O limite é uma instrução para o agente, e não um cronômetro do sistema. Para personalizar, altere o limite no `SKILL.md` e na descrição em `agents/openai.yaml`.

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

Se a bolinha não aparecer, confirme os requisitos e execute `python skills/acompanhar-demandas-longas/scripts/bubble.py outputs/demo.json` para ver o erro no terminal. Políticas ou permissões do ambiente podem impedir a janela.

## Desenvolvimento

```powershell
python -m unittest discover -s tests -v
```

Os testes cobrem a interface de linha de comando, gravação após mover a skill para outro caminho, caracteres especiais, estados e conclusão. Eles não automatizam a interface gráfica. A janela foi inspecionada manualmente em Windows com Python 3.13.

Contribuições por issues e pull requests são bem-vindas. Para bugs, informe sistema operacional, versão do Python, comando utilizado e resultado esperado, sem anexar dados privados.

## Licença

[MIT](LICENSE). Projeto independente, sem afiliação oficial com a OpenAI.
