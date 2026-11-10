/**
 * Frontend do Dashboard Executivo V-MAX.
 * Renderiza exclusivamente via Google Charts e comunica com a API FastAPI/MCP.
 * Oculta detalhes técnicos, código SQL e foca na UX de negócios.
 */

google.charts.load('current', { packages: ['corechart', 'bar', 'table'] });
google.charts.setOnLoadCallback(inicializarDashboard);

let filtroAno = '';
let filtroMes = '';

const NOMES_MESES = {
  '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr',
  '05': 'Mai', '06': 'Jun', '07': 'Jul', '08': 'Ago',
  '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez'
};

function formatarMoeda(valor) {
  if (valor === null || valor === undefined) return 'R$ 0,00';
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor);
}

function formatarNumero(valor) {
  if (valor === null || valor === undefined) return '0';
  return new Intl.NumberFormat('pt-BR').format(valor);
}

async function inicializarDashboard() {
  await carregarKPIsGerais();
  await carregarGraficoCategorias();
  await carregarGraficoEvolucaoMensal();
  await carregarComparativoAnual();
  await carregarMetricasPorUF();
  await carregarTabelaChurn();
}

function atualizarFiltrosGlobais() {
  filtroAno = document.getElementById('filtro-ano').value;
  filtroMes = document.getElementById('filtro-mes').value;

  const indicator = document.getElementById('filter-indicator');
  if (!filtroAno && !filtroMes) {
    indicator.innerText = 'Exibindo histórico consolidado completo';
  } else {
    const partes = [];
    if (filtroAno) partes.push(`Ano ${filtroAno}`);
    if (filtroMes) partes.push(`Mês ${NOMES_MESES[filtroMes] || filtroMes}`);
    indicator.innerText = `Filtrando por: ${partes.join(' | ')}`;
  }

  carregarKPIsGerais();
  carregarMetricasPorUF();
}

function limparFiltros() {
  document.getElementById('filtro-ano').value = '';
  document.getElementById('filtro-mes').value = '';
  atualizarFiltrosGlobais();
}

async function carregarKPIsGerais() {
  try {
    const params = new URLSearchParams();
    if (filtroAno) params.append('ano', filtroAno);
    if (filtroMes) params.append('mes', filtroMes);

    const qs = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`/api/kpis${qs}`);
    const data = await res.json();

    document.getElementById('kpi-gmv').innerText = formatarMoeda(data.gmv_total);
    document.getElementById('kpi-pedidos').innerText = formatarNumero(data.total_pedidos);
    document.getElementById('kpi-ticket').innerText = formatarMoeda(data.ticket_medio_geral);
    document.getElementById('kpi-leadtime').innerText = `${data.lead_time_medio_dias || 0} dias`;
  } catch (err) {
    console.error('Falha ao carregar KPIs:', err);
  }
}

async function carregarGraficoCategorias() {
  try {
    const res = await fetch('/api/analytics/gmv-categoria');
    const data = await res.json();
    const top10 = data.slice(0, 10);

    const chartData = new google.visualization.DataTable();
    chartData.addColumn('string', 'Categoria');
    chartData.addColumn('number', 'GMV (R$)');

    top10.forEach(row => {
      chartData.addRow([row.categoria, Number(row.gmv) || 0]);
    });

    const options = {
      backgroundColor: 'transparent',
      colors: ['#3b82f6'],
      legend: { position: 'none' },
      chartArea: { width: '60%', height: '80%' },
      hAxis: {
        textStyle: { color: '#94a3b8' },
        gridlines: { color: '#233152' }
      },
      vAxis: {
        textStyle: { color: '#f1f5f9' }
      }
    };

    const chart = new google.visualization.BarChart(document.getElementById('chart-categorias'));
    chart.draw(chartData, options);
  } catch (err) {
    console.error('Falha ao carregar gráfico de categorias:', err);
  }
}

async function carregarGraficoEvolucaoMensal() {
  try {
    const res = await fetch('/api/analytics/evolucao-mensal');
    const data = await res.json();

    const chartData = new google.visualization.DataTable();
    chartData.addColumn('string', 'Mês');
    chartData.addColumn('number', 'Receita Total (R$)');
    chartData.addColumn('number', 'Volume de Pedidos');

    data.forEach(row => {
      chartData.addRow([row.ano_mes, Number(row.receita_total) || 0, Number(row.volume_pedidos) || 0]);
    });

    const options = {
      backgroundColor: 'transparent',
      colors: ['#8b5cf6', '#10b981'],
      legend: { textStyle: { color: '#cbd5e1' }, position: 'top' },
      chartArea: { width: '85%', height: '70%' },
      hAxis: {
        textStyle: { color: '#94a3b8', fontSize: 11 },
        slantedText: true,
        slantedTextAngle: 45
      },
      vAxes: {
        0: { title: 'Receita (R$)', textStyle: { color: '#8b5cf6' }, gridlines: { color: '#233152' } },
        1: { title: 'Pedidos', textStyle: { color: '#10b981' }, gridlines: { color: 'transparent' } }
      },
      series: {
        0: { targetAxisIndex: 0, type: 'area' },
        1: { targetAxisIndex: 1, type: 'line' }
      }
    };

    const chart = new google.visualization.ComboChart(document.getElementById('chart-mensal'));
    chart.draw(chartData, options);
  } catch (err) {
    console.error('Falha ao carregar evolução mensal:', err);
  }
}

async function carregarComparativoAnual() {
  try {
    const res = await fetch('/api/comparativo/anual');
    const data = await res.json();

    // Organiza receita mensal por ano: { '01': { '2016': x, '2017': y, '2018': z } }
    const mapa = {};
    for (let m = 1; m <= 12; m++) {
      const mesStr = String(m).padStart(2, '0');
      mapa[mesStr] = { '2016': 0, '2017': 0, '2018': 0 };
    }

    data.forEach(item => {
      if (mapa[item.mes] && mapa[item.mes][item.ano] !== undefined) {
        mapa[item.mes][item.ano] = Number(item.gmv_total) || 0;
      }
    });

    const chartData = new google.visualization.DataTable();
    chartData.addColumn('string', 'Mês');
    chartData.addColumn('number', '2016 (R$)');
    chartData.addColumn('number', '2017 (R$)');
    chartData.addColumn('number', '2018 (R$)');

    Object.keys(mapa).sort().forEach(m => {
      chartData.addRow([
        NOMES_MESES[m] || m,
        mapa[m]['2016'],
        mapa[m]['2017'],
        mapa[m]['2018']
      ]);
    });

    const options = {
      backgroundColor: 'transparent',
      colors: ['#f59e0b', '#3b82f6', '#10b981'],
      legend: { textStyle: { color: '#cbd5e1' }, position: 'top' },
      chartArea: { width: '85%', height: '70%' },
      hAxis: { textStyle: { color: '#94a3b8' } },
      vAxis: {
        textStyle: { color: '#94a3b8' },
        gridlines: { color: '#233152' }
      }
    };

    const chart = new google.visualization.LineChart(document.getElementById('chart-comparativo-anual'));
    chart.draw(chartData, options);
  } catch (err) {
    console.error('Falha ao carregar comparativo anual:', err);
  }
}

async function carregarMetricasPorUF() {
  try {
    const qs = filtroAno ? `?ano=${filtroAno}` : '';
    const res = await fetch(`/api/metricas/uf${qs}`);
    const data = await res.json();
    const top10 = data.slice(0, 10);

    const chartData = new google.visualization.DataTable();
    chartData.addColumn('string', 'UF');
    chartData.addColumn('number', 'Faturamento (R$)');
    chartData.addColumn('number', 'Ticket Médio (R$)');

    top10.forEach(row => {
      chartData.addRow([
        row.uf,
        Number(row.gmv_total) || 0,
        Number(row.ticket_medio) || 0
      ]);
    });

    const options = {
      backgroundColor: 'transparent',
      colors: ['#06b6d4', '#ec4899'],
      legend: { textStyle: { color: '#cbd5e1' }, position: 'top' },
      chartArea: { width: '80%', height: '70%' },
      hAxis: { textStyle: { color: '#94a3b8' } },
      vAxes: {
        0: { title: 'Faturamento (R$)', textStyle: { color: '#06b6d4' }, gridlines: { color: '#233152' } },
        1: { title: 'Ticket Médio (R$)', textStyle: { color: '#ec4899' }, gridlines: { color: 'transparent' } }
      },
      series: {
        0: { targetAxisIndex: 0, type: 'bars' },
        1: { targetAxisIndex: 1, type: 'line' }
      }
    };

    const chart = new google.visualization.ComboChart(document.getElementById('chart-metricas-uf'));
    chart.draw(chartData, options);
  } catch (err) {
    console.error('Falha ao carregar métricas por UF:', err);
  }
}

async function carregarTabelaChurn() {
  try {
    const res = await fetch('/api/analytics/risco-churn');
    const data = await res.json();
    const tbody = document.querySelector('#tabela-churn tbody');
    tbody.innerHTML = '';

    data.slice(0, 15).forEach(row => {
      const tr = document.createElement('tr');
      let badgeClass = 'badge-alerta';
      if (row.classificacao_risco === 'Risco Crítico') badgeClass = 'badge-critico';
      else if (row.classificacao_risco === 'Risco Alto') badgeClass = 'badge-alto';

      tr.innerHTML = `
        <td><code style="color: #60a5fa;">${row.order_id.substring(0, 8)}...</code></td>
        <td><code>${row.customer_unique_id ? row.customer_unique_id.substring(0, 8) + '...' : '-'}</code></td>
        <td>${row.customer_state || '-'}</td>
        <td style="color: ${row.dias_atraso > 5 ? '#f87171' : '#cbd5e1'}; font-weight: 600;">
          ${row.dias_atraso !== null ? row.dias_atraso + ' d' : 'No Prazo'}
        </td>
        <td>⭐ ${row.nota_avaliacao !== null ? row.nota_avaliacao : '-'}</td>
        <td>${formatarMoeda(row.valor_total_pedido)}</td>
        <td><span class="${badgeClass}">${row.classificacao_risco}</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error('Falha ao carregar tabela de churn:', err);
  }
}

function perguntar(texto) {
  document.getElementById('ai-input').value = texto;
  enviarPergunta(texto);
}

function enviarPerguntaManual() {
  const texto = document.getElementById('ai-input').value.trim();
  if (texto) enviarPergunta(texto);
}

async function enviarPergunta(pergunta) {
  const box = document.getElementById('ai-response-box');
  const resumoDiv = document.getElementById('ai-resumo');
  const vizTitle = document.getElementById('ai-viz-title');
  const chartArea = document.getElementById('ai-chart-area');

  box.style.display = 'block';
  resumoDiv.innerHTML = '<em>Consultando assistente executivo...</em>';
  vizTitle.innerText = '';
  chartArea.innerHTML = '';

  try {
    const res = await fetch('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pergunta })
    });
    const result = await res.json();

    resumoDiv.innerHTML = result.resumo_executivo;
    vizTitle.innerText = result.titulo_visualizacao || '';

    if (!result.dados || result.dados.length === 0) {
      chartArea.innerHTML = '<p style="color: #94a3b8; padding: 20px 0;">Nenhum dado analítico encontrado para esta consulta.</p>';
      return;
    }

    renderizarVisualizacaoDinamica(chartArea, result);
  } catch (err) {
    resumoDiv.innerHTML = `<span style="color: #ef4444;">Erro ao processar consulta: ${err.message}</span>`;
  }
}

function renderizarVisualizacaoDinamica(container, result) {
  const tipo = result.tipo_grafico;

  // CASO 1: Renderização Tabular (google.visualization.Table) com tipagem dinâmica
  if (tipo === 'table') {
    const tableData = new google.visualization.DataTable();

    // Inspeciona tipos dinamicamente baseado nos dados reais da primeira linha
    const tipos = result.colunas.map((_, colIdx) => {
      const primeiroValor = result.dados.length > 0 ? result.dados[0][colIdx] : null;
      return typeof primeiroValor === 'number' ? 'number' : 'string';
    });

    result.colunas.forEach((col, idx) => {
      tableData.addColumn(tipos[idx], col);
    });

    result.dados.forEach(row => {
      const linhaFormatada = row.map((val, idx) => {
        if (tipos[idx] === 'number') {
          return val !== null && val !== undefined ? Number(val) : 0;
        }
        return val !== null && val !== undefined ? String(val) : '';
      });
      tableData.addRow(linhaFormatada);
    });

    container.innerHTML = '';
    const table = new google.visualization.Table(container);
    table.draw(tableData, {
      showRowNumber: false,
      width: '100%',
      page: 'enable',
      pageSize: 10,
      allowHtml: true
    });
    return;
  }

  // CASO 2: Gráficos (BarChart, ColumnChart, LineChart)
  // Estritamente coluna 0 = string e colunas subsequentes = number
  const chartData = new google.visualization.DataTable();
  chartData.addColumn('string', result.colunas[0]);

  for (let c = 1; c < result.colunas.length; c++) {
    chartData.addColumn('number', result.colunas[c]);
  }

  result.dados.forEach(row => {
    const label = String(row[0] ?? '');
    const metricas = row.slice(1).map(val => (val !== null && val !== undefined ? Number(val) : 0));
    chartData.addRow([label, ...metricas]);
  });

  if (tipo === 'bar') {
    const chart = new google.visualization.BarChart(container);
    chart.draw(chartData, {
      backgroundColor: 'transparent',
      colors: ['#3b82f6', '#10b981'],
      legend: { textStyle: { color: '#cbd5e1' }, position: 'top' },
      chartArea: { width: '70%', height: '80%' },
      hAxis: { textStyle: { color: '#94a3b8' }, gridlines: { color: '#233152' } },
      vAxis: { textStyle: { color: '#f1f5f9' } }
    });
  } else if (tipo === 'column') {
    const chart = new google.visualization.ColumnChart(container);
    chart.draw(chartData, {
      backgroundColor: 'transparent',
      colors: ['#06b6d4', '#8b5cf6'],
      legend: { textStyle: { color: '#cbd5e1' }, position: 'top' },
      chartArea: { width: '80%', height: '70%' },
      hAxis: { textStyle: { color: '#94a3b8', fontSize: 11 }, slantedText: true, slantedTextAngle: 45 },
      vAxis: { textStyle: { color: '#94a3b8' }, gridlines: { color: '#233152' } }
    });
  } else if (tipo === 'line') {
    const chart = new google.visualization.LineChart(container);
    chart.draw(chartData, {
      backgroundColor: 'transparent',
      colors: ['#8b5cf6', '#10b981'],
      legend: { textStyle: { color: '#cbd5e1' }, position: 'top' },
      chartArea: { width: '85%', height: '70%' },
      hAxis: { textStyle: { color: '#94a3b8' }, slantedText: true, slantedTextAngle: 45 },
      vAxis: { textStyle: { color: '#94a3b8' }, gridlines: { color: '#233152' } }
    });
  }
}
