<?xml version="1.0" encoding="UTF-8"?>
{# Validate information conditions based on file
   http://www.sat.gob.mx/informacion_fiscal/factura_electronica/Documents/Complementoscfdi/guianomina12.pdf
#}
{% if payslip.contract_id.type_id.code in ['01', '02', '03', '04', '05', '06', '07', '08'] and payslip.contract_id.tipo_regimen.clave not in ['02', '03', '04'] %}
    {% raise errors.tipo_regimen_tipo_contrato %}
{% endif %}

<cfdi:Comprobante
    xmlns:cfdi="http://www.sat.gob.mx/cfd/3"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.sat.gob.mx/cfd/3 http://www.sat.gob.mx/sitio_internet/cfd/3/cfdv32.xsd http://www.sat.gob.mx/nomina12 http://www.sat.gob.mx/sitio_internet/cfd/nomina/nomina12.xsd"
    xmlns:nomina12="http://www.sat.gob.mx/nomina12"
    Version="3.3"
    Serie="NOMINA"
    Folio="{{payslip.number or 'N/A'}}"
    Fecha="{{date}}"
    TipoDeComprobante="N"
    FormaPago="99"
    MetodoPago="PUE"
    NoCertificado="{{ certificate.serial_number }}"
    Certificado="{{ cer_data }}"
    SubTotal="{{ '{:.2f}'.format(total_percepciones + total_otrospagos) }}"
    {% if total_deducciones %} Descuento="{{ '{:.2f}'.format(total_deducciones) }}" {% endif%}
    Total="{{ '{:.2f}'.format(total_percepciones + total_otrospagos - total_deducciones) }}"
    LugarExpedicion="{{payslip.company_id.partner_id.zip}}"
    Moneda="MXN"
    Sello="@">
    <cfdi:Emisor Rfc="{{emitter.partner_id.vat}}" Nombre="{{emitter.name}}" RegimenFiscal="{{ payslip.company_id.partner_id.property_account_position_id.l10n_mx_edi_code}}"/>
    <cfdi:Receptor Rfc="{{payslip.employee_id.vat}}" Nombre="{{payslip.employee_id.name}}" UsoCFDI="P01"/>
    <cfdi:Conceptos>
        <cfdi:Concepto
            Cantidad="1"
            Descripcion="Pago de nómina"
            ValorUnitario="{{ '{:.2f}'.format(total_percepciones + total_otrospagos) }}"
            Importe="{{ '{:.2f}'.format(total_percepciones + total_otrospagos) }}"
            ClaveProdServ="84111505"
            ClaveUnidad="ACT"
            {% if total_deducciones %} Descuento="{{ '{:.2f}'.format(total_deducciones)  }}" {% endif%}/>
    </cfdi:Conceptos>
    <cfdi:Complemento>
    <nomina12:Nomina
        Version="1.2"
        TipoNomina="{{payslip.struct_id.payslip_type_id.code|required_field(errors.payslip_type)}}"
        FechaPago="{{payment_day}}"
        {%- if payslip.struct_id.payslip_type_id.code == 'O' %}
            FechaInicialPago="{{ payslip.date_from }}"
            NumDiasPagados="{{ '{:.3f}'.format(payslip.total_days) }}"
        {% else %}
            FechaInicialPago="{{ payslip.date_to }}"
            NumDiasPagados="1"
        {% endif %}
        FechaFinalPago="{{payslip.date_to}}"
        TotalPercepciones="{{ '{:.2f}'.format(total_percepciones) }}"
        {% if total_deducciones %} TotalDeducciones="{{ '{:.2f}'.format(total_deducciones) }}" {% endif %}
        {% if total_otrospagos %} TotalOtrosPagos="{{ '{:.2f}'.format(total_otrospagos) }}" {% endif %}>
      <nomina12:Emisor
        {% if payslip.contract_id.type_id.code != '09' and payslip.contract_id.type_id.code != '10'  %}
            RegistroPatronal="{{payslip.company_id.patron_registration|required_field(errors.employer_number)}}"
        {% endif %}
        {% if payslip.company_id.partner_id.property_account_position_id.l10n_mx_edi_code == '612' %}
            Curp="{{payslip.company_id.curp|required_field(errors.company_curp)}}"
        {% endif %}>
        {% if payslip.source_resource %}
            <nomina12:EntidadSNCF
                OrigenRecurso="{{ payslip.source_resource }}" {% if payslip.amount_sncf %} MontoRecursoPropio="{{ '{:.2f}'.format(payslip.amount_sncf) }}" {% endif %}/>
        {% endif %}
        </nomina12:Emisor>
      <nomina12:Receptor
        Curp="{{payslip.employee_id.curp}}"
        TipoContrato="{{payslip.contract_id.type_id.code|required_field(errors.contract_type)}}"
        TipoRegimen="{{payslip.contract_id.tipo_regimen.clave}}"
        NumEmpleado="{{payslip.employee_id.work_number}}"
        {%- if payslip.employee_id.department_id %} Departamento="{{payslip.employee_id.department_id.name}}"{% endif %}
        {%- if payslip.employee_id.job_id %} Puesto="{{payslip.employee_id.job_id.name}}"{% endif %}
        {%- if payslip.struct_id.payslip_type_id.code == 'O' %}
            PeriodicidadPago="{{payslip.contract_id.isr_table.code}}"
        {% else %}
            PeriodicidadPago="99"
        {% endif %}
        {%- if payslip.payment_type and payslip.payment_type.name == '03' %}
            Banco="{{ payslip.employee_id.bank_account_id.bank.sat_code|required_field(errors.bank_account) }}"
        {% endif %}
        ClaveEntFed="{{payslip.company_id.partner_id.state_id.code}}"
        {% if payslip.contract_id.type_id.code != '09' and payslip.contract_id.type_id.code != '10'  %}
            NumSeguridadSocial="{{payslip.employee_id.ssnid|required_field(errors.social_security)}}"
            FechaInicioRelLaboral="{{payslip.contract_id.date_start}}"
            Antigüedad="P{{payslip.antiquity}}W"
            {%- if payslip.employee_id.syndicated %} Sindicalizado="Sí"{% endif %}
            RiesgoPuesto="{{payslip.contract_id.riesgo_puesto.clave|default('1', true)}}"
            SalarioBaseCotApor="{{ '{:.2f}'.format(payslip.contract_id.integrated_wage) }}"
            SalarioDiarioIntegrado="{{ '{:.2f}'.format(payslip.contract_id.integrated_wage) }}"
        {% endif %}
        />
      <nomina12:Percepciones
        TotalGravado="{{ '{:.2f}'.format(percepciones_totalgravado) }}"
        TotalExento="{{ '{:.2f}'.format(percepciones_totalexento) }}"
        TotalSueldos="{{ '{:.2f}'.format(percepciones_totalgravado + percepciones_totalexento) }}">
        {% for line in payslip.line_ids -%}
            {% if line.category_id.code == 'PERGRA' %}
                <nomina12:Percepcion
                    TipoPercepcion="{{line.salary_rule_id.code_sat}}"
                    Clave="{{line.code}}"
                    Concepto="{{line.name}}"
                    ImporteGravado="{{ '{:.2f}'.format(line.taxable_amount) }}"
                    ImporteExento="{{ '{:.2f}'.format(line.total - line.taxable_amount) }}">
                    {% if line.salary_rule_id.code_sat == '019' %}
                        <nomina12:HorasExtra
                            Dias="{{ '{:.0f}'.format(days_overtime(line)) }}"
                            TipoHoras="{{line.salary_rule_id.overtime_type_id.code}}"
                            HorasExtra="{{ '{:.0f}'.format(hours_overtime(line)) }}"
                            ImportePagado="{{ '{:.2f}'.format(line.total) }}"/>
                    {% endif %}
                </nomina12:Percepcion>
            {% endif %}
        {%- endfor %}
      </nomina12:Percepciones>
    {% if total_deducciones %}
        <nomina12:Deducciones
            {% if TotalImpuestosRetenidos > 0 %}
                TotalImpuestosRetenidos="{{ '{:.2f}'.format(TotalImpuestosRetenidos) }}"
            {% endif %}
            TotalOtrasDeducciones="{{ '{:.2f}'.format(total_other_ded) }}">
            {% for line in payslip.line_ids -%}
                {% if line.category_id.code == 'DEDC' and line.total %}
                    <nomina12:Deduccion
                        TipoDeduccion="{{line.salary_rule_id.code_sat}}"
                        Clave="{{line.code}}"
                        Concepto="{{line.name}}"
                        Importe="{{ '{:.2f}'.format(line.total) }}" />
                {% endif %}
            {%- endfor %}
        </nomina12:Deducciones>
    {% endif %}
      {% if has_other %}
        <nomina12:OtrosPagos>
            {% for line in payslip.line_ids -%}
                {% if line.category_id.code == 'OTROS' %}
                    <nomina12:OtroPago
                        TipoOtroPago="{{line.salary_rule_id.salary_payment_type_id.code}}"
                        Clave="{{line.code}}"
                        Concepto="{{line.name}}"
                        Importe="{{ '{:.2f}'.format(line.total) }}">
                        {% if line.salary_rule_id.code == 'ISRSUB' %}
                            <nomina12:SubsidioAlEmpleo
                                SubsidioCausado="{{ '{:.2f}'.format(line.total) }}" />
                        {% endif %}
                    </nomina12:OtroPago>
                {% endif %}
            {%- endfor %}
        </nomina12:OtrosPagos>
      {% endif %}
    </nomina12:Nomina>
  </cfdi:Complemento>
</cfdi:Comprobante>
