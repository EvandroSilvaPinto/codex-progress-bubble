---
name: acompanhar-demandas-longas
description: Use when a requested task is estimated to take more than 30 seconds to deliver, or when an ongoing task exceeds 30 seconds, across projects and task types. Also applies when the user requests an HTML status page or progress bar for a demand.
---

# Acompanhar demandas longas

Comportamento padrão desta skill: toda demanda com entrega estimada acima de 30 segundos deve ter uma página HTML de acompanhamento, com pelo menos uma barra de progresso, e uma bolinha flutuante no desktop Windows. Ao clicar na bolinha, mostrar um cartão com status e barra. Aplicar automaticamente, sem exigir invocação explícita ou confirmação. Continuar o trabalho principal até a entrega.

## Ativação

- Se a estimativa inicial superar 30 segundos, criar a página antes do trabalho demorado e compartilhar seu link em comentário.
- Se a tarefa inicialmente parecer curta e ultrapassar 30 segundos, criar a página assim que perceber isso.
- Se o usuário explicitamente dispensar o acompanhamento, respeitar sua instrução.

## Página obrigatória

### Bolinha flutuante no Windows

Usar o helper incluído com Python já instalado (Tkinter), sem instalar programas ou alterar políticas do Windows. Resolver `scripts/status.py` a partir do diretório desta skill. Substituir o marcador pelo caminho real da pasta que contém este SKILL.md, em qualquer local de instalação. Exemplo de criação:

```powershell
python "<diretorio-absoluto-desta-skill>/scripts/status.py" --output outputs/status-demanda.html --title "Preparando relatório" --percent 10 --message "Trabalho iniciado" --open
```

O helper grava HTML e JSON lado a lado e abre a bolinha sem console. Ela fica por cima das janelas, pode ser arrastada e lê o JSON a cada 2 segundos. Clique abre/recolhe o cartão; × fecha a janela; o cartão também abre o HTML. Verde indica conclusão, rosa indica falha. Manter a bolinha disponível ao concluir até o usuário fechá-la.

Nas atualizações, repetir o comando com o MESMO caminho, título, novo percentual e mensagem, sem `--open`. Informar `--status` quando necessário: `"Aguardando informação"`, `"Concluído"`, `"Interrompido"` ou `"Falha"`. Para concluir, usar `--percent 100 --status "Concluído"`. A opção `--open` não duplica uma janela já aberta para o mesmo JSON. Se o usuário fechar, continuar atualizando o HTML sem reabrir automaticamente durante essa demanda.

Cada demanda deve usar seu próprio par de arquivos. O helper usa o fuso local: se o fuso do host divergir do usuário, ajustar o campo de horário nos arquivos ou adaptar o helper antes de usar. Se não houver Windows, Python/Tkinter ou desktop acessível, fornecer o HTML e informar brevemente a limitação. Não afirmar que a bolinha abriu apenas porque o processo foi iniciado; verificar quando houver ferramentas de UI.

Criar um HTML independente por demanda, com nome identificável, no diretório de entregáveis do ambiente (normalmente outputs/). Respeitar as regras de caminhos do projeto e preservar os acompanhamentos de outras demandas.

Incluir:

- Título curto da demanda.
- Status geral: Em andamento, Aguardando informação, Concluído, Interrompido ou Falha.
- Barra visível e acessível usando o elemento progress, com máximo 100, e percentual textual identificado como estimativa.
- Uma frase simples sobre o andamento; não é necessário detalhar cada etapa.
- Data e hora da última atualização no fuso do usuário.

Usar layout legível em celular e desktop, CSS embutido e nenhuma dependência externa. Escapar textos inseridos no HTML. Durante a execução, incluir uma meta tag http-equiv="refresh" com content="20" para recarregar o arquivo atualizado no navegador. Remover a recarga ao encerrar. A recarga só lê a versão salva: o agente precisa atualizar o arquivo efetivamente.

Compartilhar um link clicável com caminho absoluto logo na criação. Se a visualização disponível não recarregar automaticamente, informar que o usuário pode reabrir o link ou atualizar o navegador. Só prometer atualização ao vivo quando houver um mecanismo comprovado.

## Atualizações

Atualizar o mesmo arquivo a cada avanço relevante e buscar intervalos de aproximadamente 30 segundos enquanto estiver executando ativamente. Usar chamadas não bloqueantes ou esperas curtas quando as ferramentas permitirem. Durante uma chamada longa sem possibilidade de intervenção, atualizar imediatamente antes e depois; não inventar atualizações nesse intervalo.

O percentual representa uma estimativa do trabalho realizado. Usar marcos amplos ajustados à demanda, por exemplo: 10% iniciado, 40% em execução, 75% em revisão, 100% concluído. Não animar crescimento artificial nem avançar apenas pelo relógio. Reservar 100% para a entrega efetivamente concluída e verificada.

Se houver bloqueio ou informação pendente, manter o percentual realista e registrar o status. Se falhar ou for interrompida, registrar o resultado e a última atualização, sem marcar como concluída. Atualizar ao retomar.

Ao concluir, salvar 100%, status Concluído e uma frase de resultado; incluir links para os entregáveis quando disponíveis. Verificar o arquivo salvo e manter o link na resposta final se útil. A página não executa trabalho em segundo plano após o encerramento da conversa.

## Limites

Criar somente o acompanhamento necessário. Não publicar, abrir portas ou instalar serviços para isso. Não expor credenciais, dados sensíveis ou detalhes internos desnecessários. O HTML complementa as atualizações da conversa.
