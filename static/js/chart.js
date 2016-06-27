function productChartHandler(data) {
    $(function () {
        $('#container').highcharts({
            title: {
                text: 'Price chart',
                x: -20 //center
            },
            xAxis: {
                categories: data['dates']
            },
            yAxis: {
                plotLines: [{
                    value: 0,
                    width: 1,
                    color: '#808080'
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