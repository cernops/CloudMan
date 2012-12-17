function initPieChart(divId, title){
   pie_chart = new Highcharts.Chart({
      chart: {
         renderTo: divId,
         plotBackgroundColor: null,
         plotBorderWidth: null,
         plotShadow: false
      },
      title: {
         text: title
      },
      tooltip: {
         formatter: function() {
            return '<b>'+ this.point.name +'</b>: '+ Highcharts.numberFormat(this.percentage, 3) +' %';
         }
      },
      plotOptions: {
         pie: {
            allowPointSelect: true,
            cursor: 'pointer',
            dataLabels: {
               enabled: true,
               color: Highcharts.theme.textColor || '#000000',
               connectorColor: Highcharts.theme.textColor || '#000000',
               formatter: function() {
                  return '<b>'+ this.point.name +'</b><br/>'+ Highcharts.numberFormat(this.percentage, 3) +' %';
               },
               distance: 20
            }
         }
      }
   });
   return pie_chart;
}

