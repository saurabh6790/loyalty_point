cur_frm.cscript.type = function(doc, dt, dn){
	frappe.call({
		method: "loyalty_point_engine.loyalty_point_engine.doctype.rule.rule.get_vsibility_setting",
		args: {"rule_type": doc.type},
		callback: function(r){
			set_visibility(r.message[0], r.message[1])
		}
	})
}

set_visibility = function(hide_field_list, unhide_field_list){
	hide_field(hide_field_list)
	unhide_field(unhide_field_list)
}

cur_frm.cscript.refresh = function(doc, dt, dn){ 
	if(!doc.__islocal){cur_frm.cscript.type(doc, dt, dn) }
}