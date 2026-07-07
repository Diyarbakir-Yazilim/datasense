import React from 'react';
import ReactECharts from 'echarts-for-react';
import { FiBarChart2 } from 'react-icons/fi';

export default function DataVisualizer({ data }) {
  if (!data?.chart_data) {
    return (
      <div className="glass-panel fade-in" style={{ marginTop: '24px', textAlign: 'center', padding: '40px' }}>
        Grafik verisi bekleniyor veya oluşturulamadı...
      </div>
    );
  }

  const { correlation_matrix, target_distribution, scatter_plot } = data.chart_data;

  const commonToolbox = {
    feature: {
      saveAsImage: { 
        name: 'datasense_chart', 
        pixelRatio: 2,
        backgroundColor: '#0F172A' // Dark background for white text visibility
      }
    },
    iconStyle: { borderColor: 'rgba(255,255,255,0.7)' }
  };

  // Correlation Heatmap Options
  let heatmapOptions = null;
  if (correlation_matrix && correlation_matrix.columns) {
    const cols = correlation_matrix.columns;
    const heatmapData = [];
    for (let i = 0; i < cols.length; i++) {
      for (let j = 0; j < cols.length; j++) {
        heatmapData.push([j, i, correlation_matrix.values[i][j] !== null ? Number(correlation_matrix.values[i][j]).toFixed(2) : 0]);
      }
    }

    heatmapOptions = {
      toolbox: commonToolbox,
      tooltip: { position: 'top' },
      grid: { height: '65%', top: '15%' },
      xAxis: {
        type: 'category',
        data: cols,
        splitArea: { show: true },
        axisLabel: { color: 'rgba(255,255,255,0.7)', rotate: 45, interval: 0, fontSize: 10 }
      },
      yAxis: {
        type: 'category',
        data: cols,
        splitArea: { show: true },
        axisLabel: { color: 'rgba(255,255,255,0.7)', fontSize: 10 }
      },
      visualMap: {
        show: false,
        min: -1,
        max: 1,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '0%',
        inRange: {
          color: ['#131A26', '#3B82F6', '#00F0FF']
        },
        textStyle: { color: 'rgba(255,255,255,0.7)' }
      },
      series: [{
        name: 'Korelasyon',
        type: 'heatmap',
        data: heatmapData,
        label: { show: true, color: '#fff', fontSize: 10 },
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' }
        }
      }]
    };
  }

  // Target Distribution Options
  let distOptions = null;
  if (target_distribution) {
    if (target_distribution.type === 'categorical') {
      const pieData = target_distribution.labels.map((lbl, idx) => ({
        name: lbl,
        value: target_distribution.values[idx]
      }));
      distOptions = {
        toolbox: commonToolbox,
        tooltip: { trigger: 'item' },
        legend: { type: 'scroll', top: '10%', left: 'center', textStyle: { color: '#fff' } },
        series: [
          {
            name: 'Dağılım',
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['50%', '60%'],
            itemStyle: {
              borderRadius: 10,
              borderColor: '#131A26',
              borderWidth: 2
            },
            label: { show: false },
            data: pieData
          }
        ]
      };
    } else if (target_distribution.type === 'numerical') {
       const sortedVals = [...target_distribution.values].sort((a,b) => a-b);
       const xData = sortedVals.map((_, i) => i);
       distOptions = {
          toolbox: commonToolbox,
          tooltip: { trigger: 'axis', formatter: '{b0}: {c0}' },
          xAxis: { type: 'category', data: xData, show: false },
          yAxis: { type: 'value', axisLabel: { color: 'rgba(255,255,255,0.7)' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } } },
          series: [{
             data: sortedVals,
             type: 'line',
             smooth: true,
             areaStyle: {
                color: {
                   type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
                   colorStops: [{ offset: 0, color: '#7000FF' }, { offset: 1, color: 'transparent' }]
                }
             },
             lineStyle: { color: '#00F0FF' },
             symbol: 'none'
          }]
       };
    }
  }

  // Scatter Plot Options
  let scatterOptions = null;
  if (scatter_plot && scatter_plot.data && scatter_plot.data.length > 0) {
     scatterOptions = {
        toolbox: commonToolbox,
        tooltip: {
            trigger: 'item',
            formatter: function (params) {
                return `${scatter_plot.x_col}: ${params.data[0]}<br/>${scatter_plot.y_col}: ${params.data[1]}`;
            }
        },
        xAxis: { type: 'value', name: scatter_plot.x_col, nameTextStyle: { color: '#fff' }, axisLabel: { color: 'rgba(255,255,255,0.7)' }, splitLine: { show: false } },
        yAxis: { type: 'value', name: scatter_plot.y_col, nameTextStyle: { color: '#fff' }, axisLabel: { color: 'rgba(255,255,255,0.7)' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } } },
        series: [{
            symbolSize: 8,
            data: scatter_plot.data,
            type: 'scatter',
            itemStyle: {
               color: '#00F0FF',
               opacity: 0.7
            }
        }]
     };
  }

  return (
    <div className="glass-panel fade-in" style={{ marginTop: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <FiBarChart2 size={24} className="gradient-text" />
        <h3 style={{ margin: 0 }}>Görselleştirme & Analiz</h3>
      </div>
      
      <div className="dashboard-grid">
        <div style={{ 
          background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px', padding: '24px', minHeight: '350px'
        }}>
          <h4 style={{ color: 'var(--text-secondary)', marginBottom: '16px', textAlign: 'center' }}>Hedef Değişken Dağılımı</h4>
          {distOptions ? (
             <ReactECharts option={distOptions} style={{ height: '300px', width: '100%' }} />
          ) : (
             <p style={{ textAlign: 'center', color: 'rgba(255,255,255,0.4)', marginTop: '50px' }}>Dağılım verisi oluşturulamadı.</p>
          )}
        </div>
        
        <div style={{ 
          background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px', padding: '24px', minHeight: '350px'
        }}>
          <h4 style={{ color: 'var(--text-secondary)', marginBottom: '16px', textAlign: 'center' }}>Korelasyon Matrisi</h4>
          {heatmapOptions ? (
             <ReactECharts option={heatmapOptions} style={{ height: '350px', width: '100%' }} />
          ) : (
             <p style={{ textAlign: 'center', color: 'rgba(255,255,255,0.4)', marginTop: '50px' }}>Sayısal değişken bulunamadı.</p>
          )}
        </div>

        {scatterOptions && (
           <div style={{ 
              background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '12px', padding: '24px', minHeight: '350px',
              gridColumn: '1 / -1'
           }}>
              <h4 style={{ color: 'var(--text-secondary)', marginBottom: '16px', textAlign: 'center' }}>
                 Yüksek Korelasyon Göstergesi (r={scatter_plot.correlation})
              </h4>
              <ReactECharts option={scatterOptions} style={{ height: '350px', width: '100%' }} />
           </div>
        )}
      </div>
    </div>
  );
}
