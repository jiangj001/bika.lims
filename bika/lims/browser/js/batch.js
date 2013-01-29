(function( $ ) {
$(document).ready(function(){

    _ = jarn.i18n.MessageFactory('bika');
    PMF = jarn.i18n.MessageFactory('plone');

     if($(".portaltype-batch").length == 0 &&
       window.location.href.search('portal_factory/Batch') == -1){
        $("input[id=BatchID]").after('<a style="border-bottom:none !important;margin-left:.5;"' +
                    ' class="add_batch"' +
                    ' href="'+window.portal_url+'/batches/portal_factory/Batch/new/edit"' +
                    ' rel="#overlay">' +
                    ' <img style="padding-bottom:1px;" src="'+window.portal_url+'/++resource++bika.lims.images/add.png"/>' +
                ' </a>');
        ajax_url = window.location.href.replace("/ar_add","")
                 + "/getBatches?_authenticator=" + $('input[name="_authenticator"]').val();
        if ($("#ar_0_PatientUID").length > 0) {
            ajax_url = ajax_url + "&PatientUID=" + $("#ar_0_PatientUID").val();
        }
        if ($("#ar_0_ClientUID").length > 0) {
            ajax_url = ajax_url + "&ClientUID=" + $("#ar_0_ClientUID").val();
        }
        $("input[id*=BatchID]").combogrid({
            width: "650px",
            showOn: true,
            colModel: [{'columnName':'BatchUID','hidden':true},
                       {'columnName':'BatchID','width':'16','label':_('Batch ID')},
                       {'columnName':'PatientTitle','width':'28','label':_('Patient')},
                       {'columnName':'DoctorTitle','width':'28','label':_('Doctor')},
                       {'columnName':'ClientTitle','width':'28','label':_('Client')}],
            url: ajax_url,
            select: function( event, ui ) {
                if (window.location.href.search('ar_add') > -1){  // epid ar_add
                    column = $(this).attr('name').split(".")[1];
                    if($('#ar_'+column+'_PatientID').length > 0){
                        $('#ar_'+column+'_PatientID').val(ui.item.PatientID);
                    }
                    if($('#ar_'+column+'_DoctorID').length > 0){
                        $('#ar_'+column+'_DoctorID').val(ui.item.DoctorID);
                    }
                    if($('#ar_'+column+'_ClientID').length > 0){
                        $('#ar_'+column+'_ClientID').val(ui.item.ClientID);
                    }
                }
                $(this).val(ui.item.BatchID);
                $(this).change();
                return false;
            }
        });
    }

    if($(".portaltype-batch").length > 0 && $(".template-base_edit").length > 0) {
        $.ajax({
            url: window.location.href
                       .split("?")[0]
                       .replace("/base_edit", "")
                       .replace("/edit", "") + "/getBatchInfo",
            type: 'POST',
            data: {'_authenticator': $('input[name="_authenticator"]').val()},
            dataType: "json",
            success: function(data, textStatus, $XHR){
                $(".jsClientTitle").remove();
                $("#archetypes-fieldname-ClientID").append("<span class='jsClientTitle'>"+data['Client']+"</span>");
                $(".jsPatientTitle").remove();
                $("#archetypes-fieldname-PatientID").append("<span class='jsPatientTitle'>"+data['Patient']+"</span>");
                $(".jsDoctorTitle").remove();
                $("#archetypes-fieldname-DoctorID").append("<span class='jsDoctorTitle'>"+data['Doctor']+"</span>");
            }
        });
    }


    $('a.add_batch').prepOverlay(
        {
            subtype: 'ajax',
            filter: 'head>*,#content>*:not(div.configlet),dl.portalMessage.error,dl.portalMessage.info',
            formselector: '#batch-base-edit',
            closeselector: '[name="form.button.cancel"]',
            width:'70%',
            noform:'close',
            config: {
                onLoad: function() {
                    // manually remove remarks
                    this.getOverlay().find("#archetypes-fieldname-Remarks").remove();
//                  // display only first tab's fields
//                  $("ul.formTabs").remove();
//                  $("#fieldset-schemaname").remove();
                },
                onClose: function(){
                    // here is where we'd populate the form controls, if we cared to.
                }
            }
        }
    );

    $('input[name="PatientBirthDate"]').live('change', function(){
    	setPatientAgeAtCaseOnsetDate();
    });

	$("#OnsetDate").live('change', function(){
		setPatientAgeAtCaseOnsetDate();
	});
	
	$("#PatientID").live('change', function(){
		setPatientAgeAtCaseOnsetDate();
		$.ajax({
            type: 'POST',
            url: window.location.href.split("/batches")[0] 
					+ "/patients/" + $(this).val()
					+ "/getLastReferralId",
            data: {'_authenticator': $('input[name="_authenticator"]').val()},
            dataType: "json",
	        success: function(data){
				$("#ClientID").val(data["clientid"]);
				$(".jsClientTitle").remove();
				$("#archetypes-fieldname-ClientID").append("<span class='jsClientTitle'>"+data["clientname"]+"</span>");
			},
        });
	});

	function setPatientAgeAtCaseOnsetDate() {
		var now = new Date($("#OnsetDate").val());
		var dob = new Date($('input[name="PatientBirthDate"]').val());
		if (now!= undefined && now != null && dob!=undefined && dob != null	&& now >= dob){
			var currentday=now.getDate();
			var currentmonth=now.getMonth()+1;
			var currentyear=now.getFullYear();
			var birthday=dob.getDate();
			var birthmonth=dob.getMonth()+1;
			var birthyear=dob.getFullYear();
  		    var ageday = currentday-birthday;
			var agemonth=0;
			var ageyear=0;

			if (ageday < 0) {
				currentmonth--;
				if (currentmonth < 1) {
					currentyear--;
					currentmonth = currentmonth + 12;
				}
				dayspermonth = 30;
				if (currentmonth==1 || currentmonth==3 ||
					currentmonth==5 || currentmonth==7 ||
					currentmonth==8 || currentmonth==10||
					currentmonth==12) {
					dayspermonth = 31;
				} else if (currentmonth == 2) {
					dayspermonth = 28;
			        if(!(currentyear%4) && (currentyear%100 || !(currentyear%400))) {
			        	dayspermonth++;
			        }
			    }
				ageday = ageday + dayspermonth;
			}

			agemonth = currentmonth - birthmonth;
			if (agemonth < 0) {
				currentyear--;
				agemonth = agemonth + 12;
			}
			ageyear = currentyear - birthyear;

		    $("#PatientAgeAtCaseOnsetDate_year").val(ageyear);
		    $("#PatientAgeAtCaseOnsetDate_month").val(agemonth);
		    $("#PatientAgeAtCaseOnsetDate_day").val(ageday);

		} else {
			$("#PatientAgeAtCaseOnsetDate_year").val('');
		    $("#PatientAgeAtCaseOnsetDate_month").val('');
		    $("#PatientAgeAtCaseOnsetDate_day").val('');
		}
	}

    $('[name="CPD_delete"], [name="CPD_clear"]').click(function(event){
        event.preventDefault();
        if($(this).attr('name') == 'CPD_clear') {
            checked = $(this).parents('table').children('tbody').find(':checkbox');
        } else {
            checked = $(this).parents('table').children('tbody').find(':checked');
        }
        var nrs = [];
        $.each($(checked), function(i,e){
            nrs.push($(e).attr('id').split("-")[2]);
            $(e).parents('tr').remove();
        });
        $.ajax({
            type: 'POST',
            url: window.location.href.replace("/base_edit", "") + '/ajax_rm_provisional',
            data: {'nrs': $.toJSON(nrs),
                   '_authenticator': $('input[name="_authenticator"]').val()}
        });
        return false;
    });

    $('[name="CPD_delete"], [name="CPD_clear"]').click(function(event){
        event.preventDefault();
        if($(this).attr('name') == 'CPD_clear') {
            checked = $(this).parents('table').children('tbody').find(':checkbox');
        } else {
            checked = $(this).parents('table').children('tbody').find(':checked');
        }
        var nrs = [];
        $.each($(checked), function(i,e){
            nrs.push($(e).attr('id').split("-")[2]);
            $(e).parents('tr').remove();
        });
        $.ajax({
            type: 'POST',
            url: window.location.href.replace("/base_edit", "") + '/ajax_rm_provisional',
            data: {'nrs': $.toJSON(nrs),
                   '_authenticator': $('input[name="_authenticator"]').val()}
        });
        return false;
    });

    $('[name="CAE_delete"], [name="CAE_clear"]').click(function(event){
        event.preventDefault();
        if($(this).attr('name') == 'CAE_clear') {
            checked = $(this).parents('table').children('tbody').find(':checkbox');
        } else {
            checked = $(this).parents('table').children('tbody').find(':checked');
        }
        var nrs = [];
        $.each($(checked), function(i,e){
            nrs.push($(e).attr('id').split("-")[1]);
            $(e).parents('tr').remove();
        });
        $.ajax({
            type: 'POST',
            url: window.location.href.replace("/base_edit", "") + '/ajax_rm_aetiologic',
            data: {'nrs': $.toJSON(nrs),
                   '_authenticator': $('input[name="_authenticator"]').val()}
        });
        return false;
    });

    $('#casesymptomswidget [name="delete"], #casesymptomswidget [name="clear"]').click(function(event){
        event.preventDefault();
        if($(this).attr('name') == 'clear') {
            checked = $(this).parents('table').children('tbody').find(':checkbox');
        } else {
            checked = $(this).parents('table').children('tbody').find(':checked');
        }
        var nrs = [];
        $.each($(checked), function(i,e){
            nrs.push($(e).attr('id').split("-")[1]);
            $(e).parents('tr').remove();
        });
        $.ajax({
            type: 'POST',
            url: window.location.href.replace("/base_edit", "") + '/ajax_rm_symptoms',
            data: {'nrs': $.toJSON(nrs),
                   '_authenticator': $('input[name="_authenticator"]').val()}
        });
        return false;
    });

});
}(jQuery));