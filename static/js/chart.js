function productChartHandler(data, prName) {
    $(function () {
        $('#container').highcharts({
            title: {
                text: ''
            },
            xAxis: {
                categories: data['dates']
            },
            yAxis: {
                plotLines: [{
                    value: 0,
                    width: 1,
                    color: '#37474f'
                }]
            },
            legend: {
                layout: 'vertical',
                align: 'right',
                verticalAlign: 'middle',
                borderWidth: 0
            },
            series: data['prices']
        });
    });
}
