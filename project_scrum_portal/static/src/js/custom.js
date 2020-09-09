odoo.define('project_scrum_portal.project_scrum_portal', function (require) {
"use strict";

    var core = require('web.core');
    var website = require('website.website');
    var ajax = require('web.ajax');
   
    window.onload = function () {
    	if ($('#sprint_id').val()) {
    		ajax.jsonRpc("/get_sprint_data", 'call', {
				'sprint_id': $('.sprints').val(),
				}).then(function(result) {
		        var chart = new CanvasJS.Chart("chartContainer", {
		          theme: "light2",
		                
		          title:{
//		            text: "Burndownchart"
		          },
		          exportEnabled: true,
		          width:800,
		          data: [  //array of dataSeries     
		          { //dataSeries - first quarter
		     /*** Change type "column" to "bar", "area", "line" or "pie"***/
		           type: "line",
		           name: "Remaining Points",
		           
		           showInLegend: true,
		           dataPoints: result['remaining_points']
		         },
		
		         { //dataSeries - second quarter
		
		          type: "line",
		          name: "Hours Left", 
		          
		          showInLegend: true,               
		          dataPoints: result['remaining_hours']
		        }
		        ],
		      
		      });
	
		    chart.render();
			});
    		
			ajax.jsonRpc("/get_sprint_data", 'call', {
				'sprint_id': $('.sprints').val(),
				}).then(function(result) {
		        var chart = new CanvasJS.Chart("chartContainer2", {
		          theme: "light2",
		          exportEnabled: true,
		          width:800,
		          data: [  //array of dataSeries     
		          { //dataSeries - first quarter
		     /*** Change type "column" to "bar", "area", "line" or "pie"***/
		           type: "column",
		           name: "Remaining Points",
		           showInLegend: true,
		           dataPoints: result['remaining_points']
		         },
		
		         { //dataSeries - second quarter
		
		          type: "column",
		          name: "Hours Left", 
		          showInLegend: true,
		          dataPoints: result['remaining_hours']
		        }
		        ],
		      
		      });
	
	    chart.render();
		});
			
			ajax.jsonRpc("/get_sprint_data", 'call', {
	    		'sprint_id': $('.sprints').val(),
	    		}).then(function(result) {
	    			var chart = new CanvasJS.Chart("chartContainer1", {
	    				theme: "light2", // "light2", "dark1", "dark2"
	    				animationEnabled: false, // change to true		
	    				exportEnabled: true,
	    				width:800,
	    				data: [
	    				{
	    					type: "pie",
	    					toolTipContent: "{label}: <strong>{y}</strong>",
	    					indexLabel: "{label} : {y}",
	    					dataPoints: result['remaining_points']
	    				}
	    				]
	    			});
	    			chart.render();
	    		});
			
    }
    	ajax.jsonRpc("/get_task_data", 'call', {
    		'project_id': $('.task_id').val(),
    		}).then(function(result) {
    			var chart = new CanvasJS.Chart("charttask", {
    				theme: "light2", // "light2", "dark1", "dark2"
    				animationEnabled: false, // change to true		
//    				title:{
//    					text: "Project Task Chart"
//    				},
    				exportEnabled: true,
    				width:800,
    				data: [
    				{
    					type: "column",
    					dataPoints: result
    				}
    				]
    			});
    			chart.render();
    		});
    
    	ajax.jsonRpc("/get_task_data", 'call', {
    		'project_id': $('.task_id').val(),
    		}).then(function(result) {
    			var chart = new CanvasJS.Chart("charttask1", {
    				theme: "light2", // "light2", "dark1", "dark2"
    				animationEnabled: false, // change to true		
    				exportEnabled: true,
    				width:800,
    				data: [
    				{
    					type: "pie",
    					toolTipContent: "{label}: <strong>{y}</strong>",
    					indexLabel: "{label} : {y}",
    					dataPoints: result
    				}
    				]
    			});
    			chart.render();
    		});
    	
    	/*ajax.jsonRpc("/get_issue_data", 'call', {
    		'project_id': $('.issue_id').val(),
    		}).then(function(result) {
    			var chart = new CanvasJS.Chart("chartissue1", {
    				theme: "light2", // "light2", "dark1", "dark2"
    				animationEnabled: false, // change to true		
    				exportEnabled: true,
    				width:800,
    				data: [
    				{
    					type: "column",
    					dataPoints: result
    				}
    				]
    			});
    			chart.render();
    		});
    	
    	ajax.jsonRpc("/get_issue_data", 'call', {
    		'project_id': $('.issue_id').val(),
    		}).then(function(result) {
    			var chart = new CanvasJS.Chart("chartissue2", {
    				theme: "light2", // "light2", "dark1", "dark2"
    				animationEnabled: false, // change to true	
    				width:800,
    				exportEnabled: true,
    				data: [
    				{
    					type: "pie",
    					toolTipContent: "{label}: <strong>{y}</strong>",
    					indexLabel: "{label} : {y}",
    					dataPoints: result
    				}
    				]
    			});
    			chart.render();
    		});*/
    	
    	
	    	ajax.jsonRpc("/get_sprint_wise_data", 'call', {
				'project_id': $('.sprint_wise_id').val(),
				}).then(function(result) {
		        var chart = new CanvasJS.Chart("chartSprint", {
		          theme: "light2",
		          exportEnabled: true,
		          width:800,
		          data: [  //array of dataSeries     
		          { //dataSeries - first quarter
		     /*** Change type "column" to "bar", "area", "line" or "pie"***/
		           type: "column",
		           name: "Estimated Hours",
		           showInLegend: true,
		           dataPoints: result['estimated_hours']
		         },
		
		         { //dataSeries - second quarter
		
		          type: "column",
		          name: "Spent Hours", 
		          showInLegend: true,
		          dataPoints: result['spent_hours']
		        }
		        ],
		      
		      });
		    chart.render();
		});
	    	
    	ajax.jsonRpc("/get_team_data", 'call', {
    		'project_id': $('.team_wise_id').val(),
    		}).then(function(result) {
    			var chart = new CanvasJS.Chart("chartteam", {
    				theme: "light2", // "light2", "dark1", "dark2"
    				animationEnabled: false, // change to true		
    				exportEnabled: true,
    				width:800,
    				data: [
    				{
    					type: "column",
    					dataPoints: result
    				}
    				]
    			});
    			chart.render();
    		});
    	
    	ajax.jsonRpc("/get_team_data", 'call', {
    		'project_id': $('.team_wise_id').val(),
    		}).then(function(result) {
    			var chart = new CanvasJS.Chart("chartteam1", {
    				theme: "light2", // "light2", "dark1", "dark2"
    				animationEnabled: false, // change to true		
    				exportEnabled: true,
    				width:800,
    				data: [
    				{
    					type: "pie",
    					toolTipContent: "{label}: <strong>{y}</strong>",
    					indexLabel: "{label} : {y}",
    					dataPoints: result
    				}
    				]
    			});
    			chart.render();
    		});
	    	
    }


    $(document).on('change', '#sprint_id', function(){
    	ajax.jsonRpc("/get_sprint_data", 'call', {
    		'sprint_id': $(this).val(),
    		}).then(function(result) {
    			var chart = new CanvasJS.Chart("chartContainer", {
  		          theme: "light2",
  		          exportEnabled: true,
  		          width:800,
  		          title:{
//  		            text: "Burndownchart"
  		          },
  		
  		          data: [  //array of dataSeries     
  		          { //dataSeries - first quarter
  		     /*** Change type "column" to "bar", "area", "line" or "pie"***/
  		           type: "line",
  		           name: "Remaining Points",
  		           showInLegend: true,
  		           dataPoints: result['remaining_points']
  		         },
  		
  		         { //dataSeries - second quarter
  		
  		          type: "line",
  		          name: "Hours Left", 
  		          showInLegend: true,               
  		          dataPoints: result['remaining_hours']
  		        }
  		        ],
  		      
  		      });
    			chart.render();
    		});
    })
    
    $(document).on('change', '#sprint_id', function(){
    	ajax.jsonRpc("/get_sprint_data", 'call', {
    		'sprint_id': $(this).val(),
    		}).then(function(result) {
    			var chart = new CanvasJS.Chart("chartContainer2", {
  		          theme: "light2",
  		          exportEnabled: true,
  		          width:800,
//  		          title:{
//  		            text: "Burndownchart Hours"
//  		          },
  		
  		          data: [  //array of dataSeries     
  		          { //dataSeries - first quarter
  		     /*** Change type "column" to "bar", "area", "line" or "pie"***/
  		           type: "column",
  		           name: "Remaining Points",
  		           showInLegend: true,
  		           dataPoints: result['remaining_points']
  		         },
  		
  		         { //dataSeries - second quarter
  		
  		          type: "column",
  		          name: "Hours Left", 
  		          showInLegend: true,               
  		          dataPoints: result['remaining_hours']
  		        }
  		        ],
  		      
  		      });
    			chart.render();
    		});
    })
    
    $(document).on('change', '#sprint_id', function(){
    	ajax.jsonRpc("/get_sprint_data", 'call', {
    		'sprint_id': $(this).val(),
    		}).then(function(result) {
    			var chart = new CanvasJS.Chart("chartContainer1", {
  		          theme: "light2",
  		          exportEnabled: true,
  		          width:800,
//  		          title:{
//  		            text: "Burndownchart Hours"
//  		          },
  		
  		          data: [  //array of dataSeries     
  		          { //dataSeries - first quarter
  		     /*** Change type "column" to "bar", "area", "line" or "pie"***/
  		           type: "pie",
  		           toolTipContent: "{label}: <strong>{y}</strong>",
				   indexLabel: "{label} : {y}",
  		           name: "Remaining Points",
  		           showInLegend: true,
  		           dataPoints: result['remaining_points']
  		         },
  		        ],
  		      
  		      });
    			chart.render();
    		});
    })
    

    $(function () {
        var kanbanCol = $('.panel-body');
//        kanbanCol.css('max-height', (window.innerHeight - 150) + 'px');

        var kanbanColCount = parseInt(kanbanCol.length);
        $('.kanban-container-fluid').css('min-width', (kanbanColCount * 350) + 'px');

        draggableInit();

//        $('.panel-heading').click(function() {
//            var $panelBody = $(this).parent().children('.panel-body');
//            $panelBody.slideToggle();
//        });
//        $(".kanban-col").find('.panel-heading').click(function() {
//        	alert("this");
//        	$(this).toggleClass('clicked');
//        });
        $('.kanban-col').on('click', function() {
            $(this).toggleClass('clicked');
        });
    });

    function draggableInit() {
        var sourceId;
        var taskId;

        $('[draggable=true]').bind('dragstart', function (event) {
            sourceId = $(this).parent().attr('id');
            taskId = $(this).attr('id')
            event.originalEvent.dataTransfer.setData("text/plain", event.target.getAttribute('id'));
        });

        $('.panel-body').bind('dragover', function (event) {
            event.preventDefault();
        });

        $('.panel-body').bind('drop', function (event) {
            var children = $(this).children();
            var targetId = children.attr('id');
             ajax.jsonRpc("/update_sprint_stage", 'call', {
        		'sprint_id': taskId,
        		'source_id': sourceId,
        		'target_id': targetId,
            }).done(function(res) {
            	if(res){
            		location.reload();
            	} else {
            	    alert("sorry!!!!! not value in json call")
            	}
	            });
             ajax.jsonRpc("/update_backlog_stage", 'call', {
         		'backlog_id': taskId,
         		'source_id': sourceId,
         		'target_id': targetId,
             }).done(function(res) {
             	if(res){
             		location.reload();
             	} else {
             	    alert("sorry!!!!! not value in json call")
             	}
 	            });
            if (sourceId != targetId) {
                var elementId = event.originalEvent.dataTransfer.getData("text/plain");

                $('#processing-modal').modal('toggle'); //before post

                // Post data 
                setTimeout(function () {
                    var element = document.getElementById(elementId);
                    children.prepend(element);
                    $('#processing-modal').modal('toggle'); // after post
                }, 1000);

            }
            
            event.preventDefault();
        });
        
    }

	$(document).ready(function() {
		
		jQuery('.btn[href^=#]').click(function(e){
		    e.preventDefault();
		    var href = jQuery(this).attr('href');
		    jQuery(href).modal('toggle');
		  });
		$('#media').carousel({
		    pause: true,
		    interval: false,
		  });
	});
 });


//optional
$('#blogCarousel').carousel({
		interval: 500000
});