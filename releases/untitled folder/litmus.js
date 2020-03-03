(function() {
	/**
	 * Litmus Object
	 * @type {[framework]}
	 */
	window.L = window.L || {};

	L.name = 'Litmus Charts';
	L.version = "0.0.1";
	L.author = "HashResearch Lab";

	// Update current url with new query string and reload
	L.updateUrl = function(uri, key, value) {
		
		var re = new RegExp("([?&])" + key + "=.*?(&|$)", "i");
		var separator = uri.indexOf('?') !== -1 ? "&" : "?";
		if (uri.match(re)) {
			return uri.replace(re, '$1' + key + "=" + value + '$2');
		}
		else {
			return uri + separator + key + "=" + value;
		}

	}

	// Convert quert string into associative array
	L.queryDict = function() {
		var queryStr = window.location.search,
			queryArr = queryStr.replace("?", "").split('&'),
			queryParams = [];

			for (var q = 0, qArrLength = queryArr.length; q < qArrLength; q++) {
				var qArr = queryArr[q].split("=");
				if(!is.empty(qArr[0]) && !is.empty(qArr[1])) {
					a = {};
					a[qArr[0]] = qArr[1];

					queryParams.push(a);
				}

			}

			return queryParams;
	}

	L.get = function() {

	      // Capture query string and initialize new object
	      var query = window.location.search;
	      var obj = {};

	      // If no query string, return empty object
	      if (query === '') return obj;

	      // Remove the '?' at front of query string
	      query = query.slice(1);

	      // Split the query string into key/value pairs (ampersand-separated)
	      query = query.split('&');

	      // Loop through each key/value pair
	      query.map(function (part) {
	        var key;
	        var value;

	        // Split each key/value pair into their separate parts
	        part = part.split('=');
	        key = part[0];
	        value = part[1];

	        // If the key doesn't exist yet, set it
	        if (!obj[key]) {
	          obj[key] = value;
	        } else {

	          // If it does already exist...

	          // If it's not an array, make it an array
	          if (!Array.isArray(obj[key])) {
	            obj[key] = [obj[key]];
	          }

	          // Push the new value to the key's array
	          obj[key].push(value);
	        }
	      });

	      // Return the query string object
	      return obj;

	}

	/**
	 * [joinTwoArray description]
	 * @param  {[type]} a [1,2,3,4]
	 * @param  {[type]} b [4,5,6,7]
	 * @return {[type]}   [[1,4], [2,5], [3,6], [4, 7]]
	 */
	L.joinTwoArray = function(a, b) { 
	    result = [];
	    for(i=0; i<a.length; ++i) {
	    	result.push([a[i], b[i]]);
	    }
	    return result;
	}



	/**
	 * [joinThreeArray description]
	 * @param  {[type]} a [1,2,3,4]
	 * @param  {[type]} b [4,5,6,7]
	 * @param  {[type]} c [4,5,6,7]
	 * @return {[type]}   [[1,4,4], [2,5,5], [3,6,6], [4,7,7]]
	 */
	L.joinThreeArray = function(a, b, c) { 
	    result = [];
	    for(i=0; i<a.length; ++i) {
	    	result.push([a[i], b[i], c[i]]);
	    }
	    return result;
	}


	/**
	 * [heatmap description]
	 * @param  {[type]} config [description]
	 * @return {[type]}        [description]
	 */
	L.heatmap = function(config) {

		yields = _.pluck(config['data'], config['text']);

		var color = d3.scale.linear()
						.domain([d3.min(yields), d3.mean(yields), d3.max(yields)])
						.range(['red', 'yellow', 'green']);

		d3.select(config['element'])
			.selectAll("div")
				.data(config['data'])
				.enter()
			.append('div')
				.attr('class', config['classname'])				
				.attr('style', function(d) {
					col = is.number(d[config['color']]) ? color(d[config['color']]) : '#607D8B';
					c = 'background-color: '+col+ '!important';
					return c;
				})
			.append('a')
				.attr('href', function(d) {
					return d[config['label']];
				})
				.attr('data-id', function(d) {
					return d[config['index']];
				})
				.attr('class', config['click'])
				.attr('data-toggle', 'tooltip')
				.attr('data-placement', 'top')
				.attr('title', function(d) {

					content = '';
					_.each(config['tooltip'], function(tip) {
						k = tip[0];
						v = tip[1];
						content = content.concat(k +' : '+ d[v] + '<br>');
					});
					return content;
				})
				.text(function(d) {
					// Leave space for exact match of work other than occurences
					return d[config['label']] +' ';
				});
		$('[data-toggle="tooltip"]').tooltip({html: true});

	}

	/**
	 * India Map Cartogram
	 * @param  {[type]} config [description]
	 * @return {[type]}        [description]
	 */
	L.indiaMap = function(config) {
		// Map plot
		yields = _.pluck(config['data'], config['text']);

		fetch_table = config['call_fn'];

		var color = d3.scale.linear()
						.domain([d3.min(yields), d3.mean(yields), d3.max(yields)])
						.range(['orange', 'yellow', 'green']);

		var coords = config['data'];
		var numformat = d3.format(',.0f');
		// By trial and error
		var longitude = function(d) { return (d.Longitude - 67) * 29; },
		    latitude  = function(d) { return (39 - d.Latitude) * 30; },
		    rscale    = function(d) { return Math.pow(d[config['text']] || 0, 0.5); };

		var locations = d3.select('.locations').selectAll('.location')
		    .data(coords, function(d) { return d[config['text']]; })
		  .enter()
		    .append('circle')
		    .attr('class', 'location')
		    .attr('cx', longitude)
		    .attr('cy', latitude)
		    .attr('fill-opacity', '0.4')
		    .attr('fill', function(d) {
		    	return is.number(d[config['text']]) ? color(d[config['text']]): '#607D8B';
		    })
		    .attr('title', function(d) {
		    	return d[config['title']];
		    })
		    .attr('r', function(d) {
		    	return (d[config['text']] / 4);
		    })
		    .on('click', function(d) { 
		    	fetch_table(d[config['tooltip']], config['element']);    
		    });
		    
		locations.append('title')
		      .text(function(d) { return d[config['tooltip']]; });
		
		$('[data-toggle="tooltip"]').tooltip({html: true});
	}


	L.legend = function(config, element) {

		min = d3.min(config['data']);
		median = d3.median(config['data']);
		max = d3.max(config['data']);

		legend_container = d3.select("span"+element)
			.append("svg").attr("xmlns","http://www.w3.org/2000/svg")
			.attr("width","220")
			.attr("height","20.0000")
			.attr("class", "legendLinear")
		gradient_container = legend_container
								.append("defs")
									.append("linearGradient")
										.attr("id","gradient_legend_a916980f-36a2-437e-bb68-9f6e888c5454")

		gradient_container.append("stop").attr("offset","0.0%").attr("stop-color","#FF0000");
		gradient_container.append("stop").attr("offset","50.0%").attr("stop-color","#FFFB00");
		gradient_container.append("stop").attr("offset","100.0%").attr("stop-color","#2F8233");

		legend_container
			.append("rect")
			.attr("fill","url(#gradient_legend_a916980f-36a2-437e-bb68-9f6e888c5454)")
			.attr("x","0")
			.attr("y","0")
			.attr("width","220")
			.attr("height","20");

		legend_container.append("text").attr("x","5").attr("y","10.0").attr("dominant-baseline","middle").attr("fill","#000").text(min);
		legend_container.append("text").attr("x","95").attr("y","10.0").attr("dominant-baseline","middle").attr("fill","#000").text(median);
		legend_container.append("text").attr("x","185").attr("y","10.0").attr("dominant-baseline","middle").attr("fill","#fff").text(max);

	}


	L.treemap = function(el, title="default", data) {

		min = _.min(_.pluck(data, 'value'));
		max = _.max(_.pluck(data, 'value'));



		Highcharts.chart(el, {
		    colorAxis: {
		    	min: min,
		    	max: max,
		        minColor: 'orange',
		        maxColor: 'green',
		    },
		    credits: {
		      enabled: false
		    },
		    series: [{
		        type: 'treemap',
		        layoutAlgorithm: 'squarified',
		        data: data
		    }],
		    title: {
		        text: title
		    }
		});
	}


	
})();