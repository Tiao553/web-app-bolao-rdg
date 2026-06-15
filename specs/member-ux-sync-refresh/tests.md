# Tests: Member UX + Result Sync Refresh

## Estrategia

Validar a entrega em quatro camadas:

1. contrato de dados
2. regras de backend
3. renderizacao frontend responsiva
4. fluxo integrado no admin e no Explore

O objetivo e garantir que a mudanca seja segura para producao, porque nao existe um ambiente de dev separado para tolerar regressao manual.

## Matriz de Testes

### 1. Classificacao mobile

1. Em viewport mobile, a linha de classificacao deve exibir a identidade visual do participante como principal referencia.
2. A posicao numerica nao deve ser o elemento dominante no mobile.
3. O desktop deve continuar mostrando a tabela/linha com a mesma semantica atual.
4. A troca visual nao pode remover o acesso a nome, grupo e pontuacao.

### 2. Ranking com breakdown

1. A resposta da API de ranking inclui os campos de breakdown.
2. A pagina de ranking renderiza:
   - exatos
   - resultado
   - Brasil
   - total
3. O campo ambigouso antigo nao aparece mais na UI.
4. Os valores exibidos na tabela batem com o calculo do backend.
5. O mobile continua legivel sem quebrar a hierarquia visual.

### 3. Integracao manual de resultados

1. Ao clicar em "rodar" no admin, o sistema busca o ultimo resultado elegivel e persiste.
2. Se o ultimo resultado do provider nao precisar ser salvo, a rotina continua procurando o proximo candidato valido.
3. Se nao houver candidato elegivel, a rotina termina sem corromper o banco e registra motivo claro.
4. A execucao nao depende de edicao manual na aba de resultados para funcionar.
5. Repetir o botao nao pode duplicar o mesmo efeito em registros ja sincronizados.

### 4. Explore com busca completa

1. A busca lista todos os palpites liberados.
2. A ordenacao segue a data do jogo.
3. A busca nao fica limitada apenas ao jogo atual, ao vivo ou proximo jogo.
4. A visibilidade continua respeitando o que esta liberado.
5. O destaque do card principal pode permanecer, mas a busca nao pode herdar a mesma limitacao.

### 5. Regressoes

1. O visual mobile geral continua consistente.
2. O admin continua acessivel para rodar a integracao.
3. Ranking, classificacao, resultados e Explore continuam abrindo sem erro de contrato.
4. Nenhuma alteracao de pontuacao ou visibilidade e feita sem cobertura automatizada.

## Casos de Teste Detalhados

### Backend

1. `GET /api/member/ranking` retorna `exactPoints`, `resultPoints`, `brazilPoints` e `totalPoints`.
2. O total do ranking e consistente com a soma das componentes calculadas.
3. O fluxo de sync manual salva o ultimo resultado elegivel e gera log auditable.
4. Quando o candidato mais recente nao e persistivel, a rotina seleciona o proximo elegivel.
5. Quando nao existe candidato elegivel, o sistema responde de forma previsivel e sem alterar dados.
6. A query de Explore entrega os palpites liberados com ordenacao cronologica.

### Frontend

1. A tela de classificacao em mobile usa a identidade visual em vez do numero da posicao como foco principal.
2. A tela de ranking mostra os campos de breakdown no desktop e no mobile.
3. O botao de integracao dispara a acao correta sem exigir input manual adicional.
4. O modal/painel de busca do Explore exibe a lista completa liberada.
5. A ordenacao da lista de busca segue a data do jogo e nao a recencia do card destacado.

### Integracao / E2E

1. Login admin -> abrir integracao -> clicar em rodar -> confirmar resultado salvo.
2. Login membro -> abrir ranking -> confirmar breakdown.
3. Login membro -> abrir classificacao no celular -> confirmar bandeira/identidade visual.
4. Login membro -> abrir Explore -> buscar -> confirmar lista completa liberada.

## Evidencias Esperadas

1. Snapshot ou screenshot da classificacao mobile com o novo comportamento.
2. Snapshot ou screenshot do ranking mostrando o breakdown de pontos.
3. Teste de integracao garantindo que o sync manual persistiu o ultimo resultado elegivel.
4. Evidencia de que a busca do Explore nao esta truncada ao jogo atual/ao vivo.
5. Evidencia de que o desktop nao sofreu regressao de layout.

## Gates de Validacao

- [ ] Existe teste de API para o ranking com breakdown.
- [ ] Existe teste de integracao para o sync manual por ultimo resultado elegivel.
- [ ] Existe teste de UI mobile para classificacao.
- [ ] Existe teste de UI para a busca completa no Explore.
- [ ] Existe validacao de que o comportamento antigo manual da pagina de resultados nao e mais necessario para o novo fluxo.
- [ ] Todos os testes passam antes de qualquer publicacao.
