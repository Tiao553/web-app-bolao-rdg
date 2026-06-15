# PRD: Member UX + Result Sync Refresh

## Metadata

| Campo | Valor |
|---|---|
| Feature | `member-ux-sync-refresh` |
| Status | Draft |
| Tipo | Ajuste funcional + UX + integracao de resultados |
| Prioridade | Alta |
| Donos provaveis | Backend + Frontend + QA |

## Objetivo

Preservar a estrutura atual da aplicacao, que ja funciona bem no celular, e corrigir quatro frentes de friccao que hoje geram confusao e trabalho manual:

1. A tela de classificacao no mobile deve trocar o numero da posicao por uma representacao visual mais rapida de ler, como a bandeira/identidade do participante.
2. A tela de ranking deve mostrar explicitamente o breakdown da pontuacao, separando exatos, resultado, Brasil e total, sem campos ambigousos como `Camp.`.
3. A integracao de resultados deve ser executada por etapas, começando por um acionamento manual em admin que busca o ultimo resultado elegivel e persiste no banco; o agendamento fica para uma fase posterior.
4. A busca do Explore deve deixar de ser limitada ao jogo atual/ao vivo/proximo e passar a listar todos os palpites liberados, ordenados por data.

## Problema

Hoje o produto esta numa zona intermediaria: a experiencia mobile e boa em varios pontos, mas algumas telas ficam densas ou pouco legiveis. Ao mesmo tempo, a integracao de resultados ainda depende de fluxo manual e nao tem um caminho claro de evolucao para operacao recorrente.

Os problemas aparecem em quatro lugares:

1. **Classificacao mobile**: o numero da posicao ocupa espaco e nao ajuda na leitura rapida. Em telas pequenas, a bandeira ou o badge do time e mais util para identificar o participante.
2. **Ranking**: a pagina mostra total, mas nao deixa claro como a pontuacao foi formada. O usuario nao entende quantos pontos vieram de exatos, placares e bonus de Brasil.
3. **Integracao de resultados**: o fluxo atual exige operacao manual na aba de resultados. Falta um caminho confiavel de "rodar agora" que leia a origem, escolha o ultimo resultado valido e salve automaticamente.
4. **Explore**: a busca esta funcionando como visao de destaque do momento, nao como exploracao completa de palpites liberados. O usuario precisa enxergar a lista inteira, filtrada por liberacao e ordenada por data.

## Evidencia Atual

1. A classificacao mobile hoje prioriza layout compacto, mas a leitura da posicao numerica nao e a melhor opcao em telas pequenas.
2. O ranking ja possui a informacao de pontuacao, mas o contrato e a UI nao deixam o breakdown totalmente explicito.
3. A integracao de resultados ja existe em producao, mas o disparo manual ainda nao garante que o sistema escolha automaticamente o ultimo resultado que realmente precisa ser persistido.
4. O Explore ja possui busca, porem a logica precisa refletir visibilidade ampla dos palpites liberados, e nao apenas cards do jogo em destaque.

## Resultado Esperado

1. O mobile de classificacao continua com a mesma estrutura geral, mas a identidade visual do participante fica mais rapida de identificar que o numero da posicao.
2. O ranking mostra claramente:
   - pontos de exatos
   - pontos de resultado
   - pontos de Brasil
   - total consolidado
3. O botao de admin para integracao dispara uma rotina que:
   - consulta a origem
   - encontra o ultimo resultado elegivel
   - grava a mudanca no banco
   - registra auditoria suficiente para validar o que aconteceu
4. A busca do Explore lista todos os palpites liberados, em ordem cronologica, sem esconder jogos liberados que nao sejam os mais recentes.

## Escopo

### Incluido

1. Ajuste da renderizacao mobile da tela de classificacao.
2. Ajuste do contrato e da UI do ranking para exibir breakdown de pontos.
3. Ajuste do fluxo de integracao de resultados para um disparo manual por etapa.
4. Ajuste do Explore para busca completa dos palpites liberados.
5. Cobertura automatizada de backend, contrato e frontend para os quatro fluxos.

### Excluido

1. Reescrever a regra de pontuacao do jogo.
2. Mudar o visual base do app em desktop.
3. Implementar agendamento recorrente completo nesta entrega.
4. Reescrever o motor de resultados manual da pagina de resultados.
5. Alterar o tratamento de artilharia como feature separada, exceto se necessario para manter consistencia de contrato.

## Requisitos Funcionais

### 1. Classificacao mobile

1. Em telas pequenas, a linha de classificacao deve destacar a identidade do participante em vez de mostrar a posicao numerica como elemento principal.
2. A apresentacao mobile nao deve quebrar o layout atual da tabela/cartao.
3. Desktop deve manter o comportamento atual, salvo pequenos ajustes de alinhamento se necessario.
4. A leitura da classificacao precisa continuar permitindo identificar rank, nome e pontuacao sem ambiguidade.

### 2. Ranking com breakdown

1. A tabela de ranking deve exibir campos claros para:
   - exatos
   - resultado
   - Brasil
   - total
2. O campo que hoje causa duvida, como `Camp.`, precisa ser removido ou substituido por um nome sem ambiguidade de negocio.
3. A soma exibida deve ser consistente com os dados calculados no backend.
4. A pagina deve continuar suportando a visualizacao responsiva sem transformar a tabela em um bloco confuso no mobile.

### 3. Integracao de resultados por etapas

1. O botao de rodar na aba de integracao precisa executar um fluxo de sincronizacao manual focado no ultimo resultado elegivel.
2. O backend deve escolher automaticamente qual resultado persistir, em vez de depender de entrada manual na tela de resultados.
3. Se o ultimo resultado do provider nao precisar ser persistido, o sistema deve procurar o proximo candidato elegivel dentro da mesma rotina.
4. A execucao deve ser idempotente no limite do possivel: clicar novamente nao pode gerar duplicidade ou corromper o estado.
5. O fluxo deve registrar logs suficientes para diagnostico em producao, ja que nao existe ambiente de dev isolado.

### 4. Explore com busca completa

1. A busca deve listar todos os palpites liberados, e nao apenas o card do jogo atual ou o proximo jogo.
2. A ordenacao primaria deve ser por data do jogo.
3. O resultado da busca precisa seguir a visibilidade do sistema: liberar o que esta liberado, esconder o que ainda nao pode aparecer.
4. O comportamento de destaque do jogo atual pode permanecer no topo do Explore principal, mas nao pode limitar a busca.

## Requisitos Nao Funcionais

1. A estrutura mobile que ja funciona bem deve ser preservada; a entrega e correcao cirurgica, nao redesign.
2. O novo fluxo de integracao precisa ser seguro para producao, pois nao ha ambiente de dev dedicado.
3. O contrato backend/frontend deve ser explicito o bastante para evitar regressao silenciosa.
4. As mudancas precisam ser cobertas por testes automatizados antes de qualquer dependencia em agendamento recorrente.

## Proposta de Implementacao por Fases

### Fase 1: Dados, contrato e UI

1. Expor no backend os pontos detalhados do ranking.
2. Ajustar a UI do ranking para usar os novos campos.
3. Ajustar a classificacao mobile para trocar a posicao numerica pela identidade visual apropriada.
4. Ajustar a busca do Explore para usar a colecao liberada e ordenacao cronologica.

### Fase 2: Integracao manual por botao

1. Reaproveitar o fluxo existente de admin integracao.
2. Introduzir uma rotina que selecione o ultimo resultado elegivel para persistencia.
3. Exibir no admin a resposta da execucao e o log necessario para auditoria.

### Fase 3: Agendamento

1. Depois que o fluxo manual estiver validado, habilitar agendamento recorrente.
2. O agendamento deve ser implementado como codigo/configuracao da aplicacao, sem depender de operacao manual obscura na plataforma.
3. Esta fase so entra depois de validar que o fluxo manual nao quebra o banco nem o contrato.

## Arquivos Mais Provaveis de Impacto

1. `backend/app/api/routes/member.py`
2. `backend/app/api/routes/admin.py`
3. `backend/app/services/sync_service.py`
4. `app/src/lib/contracts.ts`
5. `app/src/app/(member)/ranking/page.tsx`
6. `app/src/app/(member)/standings/page.tsx`
7. `app/src/app/(member)/explore/explore-client.tsx`
8. `app/src/components/admin/integration-controls.tsx`
9. `backend/tests/integration/test_admin_sync.py`
10. `backend/tests/integration/test_member_access.py`

## Riscos

1. Mostrar bandeira no mobile pode piorar acessibilidade se nao houver texto auxiliar ou label semantica.
2. Expor breakdown de ranking pode gerar confusao se o contrato e a UI nao estiverem 100% alinhados.
3. O fluxo de integracao pode persistir um resultado incorreto se o criterio de "ultimo elegivel" nao for estrito o bastante.
4. A busca do Explore pode virar uma lista longa demais se a ordenacao e o filtro de liberacao nao forem consistentes.

## Mitigacoes

1. Manter texto auxiliar para leitores de tela quando o numero da posicao sair da area principal.
2. Validar o contrato do ranking com teste automatizado antes de revisar a UI.
3. Registrar o motivo de cada escolha na rotina de integracao, inclusive quando um candidato for ignorado.
4. Tratar a busca do Explore como uma visao de lista, nao como um painel de destaque.

## Criticos de Aceitacao

1. No mobile, a classificacao deixa de depender da posicao numerica como principal sinal visual.
2. O ranking mostra exatos, resultado e Brasil de forma explicita.
3. O botao de integracao executa um sync manual que pega o ultimo resultado elegivel e grava no banco.
4. A busca do Explore mostra todos os palpites liberados e ordena por data.
5. Nenhuma dessas mudancas quebra a experiencia mobile que ja estava boa.

## Gates de Validacao

- [ ] Existe teste cobrindo a renderizacao mobile da classificacao.
- [ ] Existe teste cobrindo o novo contrato do ranking.
- [ ] Existe teste cobrindo o sync manual de ultimo resultado elegivel.
- [ ] Existe teste cobrindo a busca do Explore com lista completa e ordenacao cronologica.
- [ ] Existe validacao de que o desktop nao regrediu ao trocar o mobile.
- [ ] Existe evidenca de que a integracao continua segura para producao.
