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

cur_frm.cscript.onload = function(doc, dt, dn){
	var role_area = $('<div style="min-height: 160px">')
				.appendTo(cur_frm.fields_dict.modes.wrapper);
	cur_frm.mode_editor = new frappe.PaymentModes(role_area);
}

cur_frm.cscript.validate = function(doc) {
	if(cur_frm.mode_editor) {
		cur_frm.mode_editor.set_roles_in_table()
	}
}

frappe.PaymentModes = Class.extend({
	init: function(wrapper) {
		var me = this;
		this.wrapper = wrapper;
		$(wrapper).html('<div class="help">Loading...</div>')
		return frappe.call({
			method: 'loyalty_point_engine.loyalty_point_engine.custom_script_handler.get_payment_modes',
			callback: function(r) {
				me.roles = r.message;
				me.show_roles();

				// refresh call could've already happened
				// when all role checkboxes weren't created
				if(cur_frm.doc) {
					cur_frm.mode_editor.show();
				}
			}
		});
	},
	show_roles: function() {
		var me = this;
		$(this.wrapper).empty();
		// var mode_toolbar = $('<p><button class="btn btn-default btn-add"></button>\
		// 	<button class="btn btn-default btn-remove"></button></p>').appendTo($(this.wrapper));

		$.each(this.roles, function(i, role) {
			$(me.wrapper).append(repl('<div class="user-role" \
				data-user-role="%(role)s">\
				<input type="checkbox" style="margin-top:0px;"> \
				%(role)s\
			</div>', {role: role}));
		});

		$(this.wrapper).find('input[type="checkbox"]').change(function() {
			cur_frm.dirty();
		});
		// $(this.wrapper).find('.user-role a').click(function() {
		// 	me.show_permissions($(this).parent().attr('data-user-role'))
		// 	return false;
		// });
	},
	show: function() {
		var me = this;

		// uncheck all roles
		$(this.wrapper).find('input[type="checkbox"]')
			.each(function(i, checkbox) { checkbox.checked = false; });

		// set user roles as checked
		$.each((cur_frm.doc.payment_modes || []), function(i, payment_mode) {
				var checkbox = $(me.wrapper)
					.find('[data-user-role="'+payment_mode.mode+'"] input[type="checkbox"]').get(0);
				if(checkbox) checkbox.checked = true;
			});
	},
	set_roles_in_table: function() {
		var opts = this.get_roles();
		var existing_mode_map = {};
		var existing_mode_list = [];

		$.each((cur_frm.doc.payment_modes || []), function(i, payment_mode) {
				existing_mode_map[payment_mode.mode] = payment_mode.name;
				existing_mode_list.push(payment_mode.mode);
			});

		// remove unchecked roles
		$.each(opts.unchecked_modes, function(i, mode) {
			if(existing_mode_list.indexOf(mode)!=-1) {
				frappe.model.clear_doc("Payment Modes", existing_mode_map[mode]);
			}
		});

		// add new roles that are checked
		$.each(opts.checked_modes, function(i, mode) {
			if(existing_mode_list.indexOf(mode)==-1) {
				var payment_mode = frappe.model.add_child(cur_frm.doc, "Payment Modes", "payment_modes");
				payment_mode.mode = mode;
			}
		});

		refresh_field("payment_modes");
	},
	get_roles: function() {
		var checked_modes = [];
		var unchecked_modes = [];
		$(this.wrapper).find('[data-user-role]').each(function() {
			if($(this).find('input[type="checkbox"]:checked').length) {
				checked_modes.push($(this).attr('data-user-role'));
			} else {
				unchecked_modes.push($(this).attr('data-user-role'));
			}
		});

		return {
			checked_modes: checked_modes,
			unchecked_modes: unchecked_modes
		}
	}
})