// frontend/src/components/BacktestChart.tsx
import Chart from 'react-apexcharts';
import { Card } from 'antd';

interface BacktestChartProps {
  data: { time: string; price: number }[];
  trades: any[];
}

export const BacktestChart = ({ data, trades }: BacktestChartProps) => {
  // Generate annotations for Buy/Sell labels
  const points = trades.flatMap((trade) => [
    {
      x: new Date(trade.entry_time).getTime(),
      y: trade.entry_price,
      marker: { size: 6, fillBySeries: false, fillColor: '#3f8600', strokeColor: '#fff' },
      label: { text: 'BUY', style: { background: '#3f8600', color: '#fff' } }
    },
    {
      x: new Date(trade.exit_time).getTime(),
      y: trade.exit_price,
      marker: { size: 6, fillBySeries: false, fillColor: '#cf1322', strokeColor: '#fff' },
      label: { text: 'SELL', style: { background: '#cf1322', color: '#fff' } }
    }
  ]);

  const options: ApexCharts.ApexOptions = {
    chart: { type: 'line', animations: { enabled: false } },
    xaxis: { type: 'datetime' },
    stroke: { width: 2, curve: 'smooth' },
    annotations: { points },
    theme: { mode: 'dark' },
    colors: ['#646cff']
  };

  const series = [{
    name: 'Price',
    data: data.map(c => ({ x: new Date(c.time).getTime(), y: c.price }))
  }];

  return (
    <Card title="Price Action & Trade Execution">
      <Chart options={options} series={series} type="line" height={400} />
    </Card>
  );
};