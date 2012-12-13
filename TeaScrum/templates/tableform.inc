{% for field in form %}
<tr>
	<th>{{ field.label_tag }}</th>
	<td class="inc">
		{{ field }}
		{% if field.errors %}<br><span style="color:red;">{{ field.errors }}</span>{% endif %}
	</td>
	<td>{{ field.help_text }}</td>
</tr>
{% endfor %}
