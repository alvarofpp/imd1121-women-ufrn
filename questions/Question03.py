import altair as alt
import pandas as pd
import streamlit as st
from questions import Question


class Question03(Question):

    def __init__(self):
        self.pos_graduacao = [
            'LATO SENSU',
            'MESTRADO',
            'DOUTORADO',
            'STRICTO SENSU',
            'RESIDÊNCIA',
        ]

    def render(self, df):
        st.markdown('# Percentual de homens e mulheres que evadiram e concluíram, em cada nível de ensino')
        st.markdown(
            'O gráfico a seguir retrata o percentual de discentes dos sexos feminino e masculino, como também a diferença entre esses dois percentuais.')
        st.markdown('#### Como interpretar o gráfico')
        st.markdown('''
        - Na parte superior do gráfico está representado o percentual de discentes do sexo masculino, enquanto na parte inferior está expresso o percentual de discentes do sexo feminino;
        - Em amarelo está representada a diferença: se o retângulo referente à diferença estiver na parte inferior do gráfico, significa que a diferença entre os percentuais é negativa (há menos homens do que mulheres), e vice versa.
        ''')
        st.markdown(
            '**Observação**: é importante ressaltar que os valores negativos no eixo y ("% dos ingressantes"), quando estamos observando o percentual de discentes do sexo feminino, não indica um valor negativo em si - esse formato foi utilizado por limitações da ferramenta.')

        niveis = ['TÉCNICO', 'GRADUAÇÃO', 'PÓS GRADUAÇÃO']
        dfs = []

        for nivel in niveis:
            df_nivel_ensino = self._calcular_percentuais_by_nivel_ensino(df, nivel)
            df_nivel_ensino.loc[:, 'nivel_ensino'] = nivel
            dfs.append(df_nivel_ensino)

        df_chart = pd.concat(dfs)
        filter_f = df_chart['sexo'] == 'F'
        df_chart.loc[filter_f, 'percentual'] = df_chart[filter_f]['percentual'] * -1
        df_chart['sexo'] = df_chart['sexo'].replace({
            'F': 'Feminino',
            'M': 'Masculino',
        })
        df_chart['nivel_ensino'] = df_chart['nivel_ensino'].str.title()
        df_chart.loc[df_chart['sexo'].isin(['Feminino', 'Masculino']), 'size'] = 100
        df_chart.loc[df_chart['sexo'].isin(['Diferença']), 'size'] = 50

        alt_chart = alt.Chart(df_chart).mark_bar().transform_calculate(
            order='if(datum.sexo === "Feminino", 0, if(datum.sexo === "Masculino", 1, 2))'
        ).encode(
            x=alt.X('nivel_ensino:N', title=None),
            y=alt.Y('sum(percentual):Q', stack=False, title='% dos ingressantes'),
            column=alt.Column('tipo:N', title=None),
            color=alt.Color('sexo', title='Gênero',
                            scale=alt.Scale(domain=['Diferença', 'Feminino', 'Masculino'],
                                            range=['#f6c85f', '#6f4e7c', '#0b84a5'])
                            ),
            size=alt.Size('size:Q', legend=None, scale=alt.Scale(domain=[0, 40])),
            tooltip=[
                alt.Tooltip('sexo', title='Gênero'),
                alt.Tooltip('sum(percentual):Q', title='% dos ingressantes', format='.2f')
            ]
        ).properties(width=250)
        st.altair_chart(alt_chart)

    def _calcular_percentuais_by_nivel_ensino(self, df, nivel_ensino):
        if nivel_ensino == 'PÓS GRADUAÇÃO':
            df_nivel_ensino = df[df.nivel_ensino.isin(self.pos_graduacao)]
        else:
            df_nivel_ensino = df[df.nivel_ensino == nivel_ensino]

        df_evasao = df_nivel_ensino[df_nivel_ensino.status == 'CANCELADO']
        df_concluintes = df_nivel_ensino[df_nivel_ensino.status == 'CONCLUÍDO']

        return self._calcular_percentuais(df_nivel_ensino, df_evasao, df_concluintes)

    def _calcular_percentuais(self, df_total, df_evasao, df_concluintes):
        evasao_por_sexo = df_evasao.groupby(by='sexo').count()['matricula']
        concluintes_por_sexo = df_concluintes.groupby(by='sexo').count()['matricula']

        sexos = ['F', 'M']
        dados = []
        dados_diff = {}

        for sexo in sexos:
            evasao_total = evasao_por_sexo.loc[sexo]
            evasao_percent = evasao_por_sexo.loc[sexo] / evasao_por_sexo.sum() * 100

            concluintes_total = concluintes_por_sexo.loc[sexo]
            concluintes_percent = concluintes_por_sexo.loc[sexo] / concluintes_por_sexo.sum() * 100

            dados.append([sexo, evasao_total, evasao_percent, 'Evasão'])
            dados.append([sexo, concluintes_total, concluintes_percent, 'Conclusão'])
            dados_diff[sexo] = {
                'concluintes_total': concluintes_total,
                'concluintes_percent': concluintes_percent,
                'evasao_total': evasao_total,
                'evasao_percent': evasao_percent,
            }
        df_sexo = pd.DataFrame(data=dados, columns=['sexo', 'total', 'percentual', 'tipo'])

        df_sexo = df_sexo.append({
            'sexo': 'Diferença',
            'total': dados_diff['M']['evasao_total'] - dados_diff['F']['evasao_total'],
            'percentual': dados_diff['M']['evasao_percent'] - dados_diff['F']['evasao_percent'],
            'tipo': 'Evasão',
        }, ignore_index=True)

        return df_sexo.append({
            'sexo': 'Diferença',
            'total': dados_diff['M']['concluintes_total'] - dados_diff['F']['concluintes_total'],
            'percentual': dados_diff['M']['concluintes_percent'] - dados_diff['F']['concluintes_percent'],
            'tipo': 'Conclusão',
        }, ignore_index=True)
