/**
 * Frontend do Dashboard Executivo V-MAX.
 * Renderiza exclusivamente via Google Charts e comunica com a API FastAPI/MCP.
 * Oculta detalhes técnicos, código SQL e foca na UX de negócios.
 */

google.charts.load('current', { packages: ['corechart', 'bar', 'table'] });
google.charts.setOnLoadCallback(inicializarDashboard);

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
  await carregarTabelaChurn();
}

async function carregarKPIsGerais() {
  try {
    const res = await fetch('/api/kpis');
    const data = await res.json();
    document.getElementById('kpi-gmv').innerText = formatarMoeda(data.gmv_total);
    document.getElementById('kpi-pedidos').innerText = formatarNumero(data.total_pedidos);
    document.getElementById('kpi-ticket').innerText = formatarMoeda(data.ticket_medio_geral);
    document.getElementById('kpi-leadtime').innerText = `${data.lead_time_medio_dias} dias`;
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
      chartData.addRow([row.categoria, row.gmv]);
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
      chartData.addRow([row.ano_mes, row.receita_total, row.volume_pedidos]);
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
  const chartData = new google.visualization.DataTable();

  // Adiciona colunas
  result.colunas.forEach((col, idx) => {
    const tipo = (idx === 0) ? 'string' : 'number';
    chartData.addColumn(tipo, col);
  });

  // Adiciona linhas
  result.dados.forEach(row => {
    chartData.addRow(row);
  });

  const tipo = result.tipo_grafico;

  if (tipo === 'bar') {
    const chart = new google.visualization.BarChart(container);
    chart.draw(chartData, {
      backgroundColor: 'transparent',
      colors: ['#3b82f6'],
      legend: { position: 'none' },
      chartArea: { width: '70%', height: '80%' },
      hAxis: { textStyle: { color: '#94a3b8' }, gridlines: { color: '#233152' } },
      vAxis: { textStyle: { color: '#f1f5f9' } }
    });
  } else if (tipo === 'column') {
    const chart = new google.visualization.ColumnChart(container);
    chart.draw(chartData, {
      backgroundColor: 'transparent',
      colors: ['#06b6d4'],
      legend: { position: 'none' },
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
  } else {
    // Tabela padrão
    let html = '<table><thead><tr>';
    result.colunas.forEach(c => { html += `<th>${c}</th>`; });
    html += '</tr></thead><tbody>';
    result.dados.forEach(r => {
      html += '<tr>';
      r.forEach(val => {
        const texto = (typeof val === 'number') ? val.toLocaleString('pt-BR') : val;
        html += `<td>${texto}</td>`;
      });
      html += '</tr>';
    });
    html += '</tbody></table>';
    container.innerHTML = html;
  }
}
