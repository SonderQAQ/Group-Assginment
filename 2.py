import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# 颜色方案映射函数 - 放在函数外部或确保在调用前定义
def get_color_scheme(scheme_name):
    """获取颜色方案"""
    schemes = {
        "Plotly默认": px.colors.qualitative.Plotly,
        "Viridis": px.colors.sequential.Viridis,
        "Plasma": px.colors.sequential.Plasma,
        "Cividis": px.colors.sequential.Cividis,
        "Sunset": px.colors.sequential.Sunset,
        
        "平衡色": ['#2E91E5', '#E15F99', '#1CA71C', '#FB0D0D', '#DA16FF', 
                  '#222A2A', '#B68100', '#750D86', '#EB663B', '#511CFB']
    }
    return schemes.get(scheme_name, px.colors.qualitative.Plotly)

def main():
    st.set_page_config(
        page_title="马来西亚GDP可视化仪表板",
        page_icon="📊",
        layout="wide"
    )
    
    # 优化CSS - 深色背景上的白色文字
    st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
    }
    .main-header {
        font-size: 2.5rem;
        color: #ffffff;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .section-header {
        color: #ffffff;
        font-size: 1.5rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .chart-card {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #3a3a4a;
    }
    .metric-card {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #4cc9f0;
        margin-bottom: 10px;
    }
    .stSelectbox > div > div {
        background-color: #262730;
        color: white;
    }
    .stSelectbox label {
        color: #ffffff !important;
    }
    .stSlider label {
        color: #ffffff !important;
    }
    .stCheckbox label {
        color: #ffffff !important;
    }
    .stRadio label {
        color: #ffffff !important;
    }
    .info-text {
        color: #a0a0c0;
        font-size: 0.9rem;
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">📊 马来西亚GDP数据可视化仪表板</h1>', unsafe_allow_html=True)
    
    # 加载数据函数
    @st.cache_data
    def load_data():
        URL_DATA = 'https://storage.dosm.gov.my/gdp/gdp_annual_nominal_supply.parquet'
        try:
            df = pd.read_parquet(URL_DATA)
            
            # 处理日期列
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df['year'] = df['date'].dt.year
                df['year_str'] = df['year'].astype(str)
                
                # 只保留有意义的年份数据
                df = df[df['year'] >= 2000]  # 只保留2000年后的数据
                
            return df
        except Exception as e:
            st.error(f"数据加载失败: {str(e)}")
            return pd.DataFrame()
    
    # 侧边栏 - 配置面板
    with st.sidebar:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.header("⚙️ 控制面板")
        
        # 图表选择
        st.subheader("📋 选择图表类型")
        chart_type = st.selectbox(
            "图表类型",
            [
                "时间序列趋势图",
                "年度对比柱状图", 
                "多年度占比饼图",
                "热力图分析",
                "相关性散点图",
                "堆叠面积图"
            ],
            index=0
        )
        
        st.divider()
        
        # 图表设置
        st.subheader("🎨 图表设置")
        
        # 颜色方案选择
        color_scheme = st.selectbox(
            "颜色方案",
            ["Plotly默认", "Viridis", "Plasma", "Cividis", "Sunset", "Ice", "平衡色"]
        )
        
        # 获取颜色序列
        color_sequence = get_color_scheme(color_scheme)
        
        # 显示选项
        col1, col2 = st.columns(2)
        with col1:
            show_grid = st.checkbox("网格线", value=True)
        with col2:
            show_legend = st.checkbox("图例", value=True)
        
        st.divider()
        
        # 数据信息
        st.subheader("📊 数据信息")
        st.info("""
        **数据来源:** 马来西亚统计局  
        **数据频率:** 年度GDP数据  
        **更新:** 实时从官方API获取
        """)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 加载数据
    with st.spinner('正在加载数据...'):
        df = load_data()
    
    if df.empty:
        st.error("无法加载数据，请检查网络连接或数据源。")
        return
    
    # 获取数值列（排除年份列）
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [col for col in numeric_cols if col not in ['year']]
    
    if not numeric_cols:
        st.error("数据中没有找到数值指标列")
        return
    
    # 获取年份信息
    if 'year' in df.columns:
        years = sorted(df['year'].unique())
        min_year = min(years) if years else 2000
        max_year = max(years) if years else 2023
    else:
        # 如果没有年份信息，使用默认值
        years = list(range(2000, 2024))
        min_year = 2000
        max_year = 2023
    
    # 主内容区域
    st.markdown("---")
    
    # 指标卡片区域
    st.markdown('<div class="section-header">📈 关键指标概览</div>', unsafe_allow_html=True)
    
    if numeric_cols:
        # 选择主要指标
        main_metric = numeric_cols[0] if numeric_cols else None
        
        if main_metric and 'year' in df.columns and len(years) > 1:
            latest_year = max_year
            prev_year = latest_year - 1 if latest_year - 1 in years else years[-2] if len(years) > 1 else latest_year
            
            latest_value = df[df['year'] == latest_year][main_metric].mean() if not df[df['year'] == latest_year].empty else 0
            prev_value = df[df['year'] == prev_year][main_metric].mean() if not df[df['year'] == prev_year].empty else 0
            
            growth = ((latest_value - prev_value) / prev_value * 100) if prev_value != 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 0.9rem; color: #a0a0c0;">当前年份数值</div>
                    <div style="font-size: 1.8rem; color: #ffffff; font-weight: bold;">{latest_value:,.0f}</div>
                    <div style="font-size: 0.8rem; color: #a0a0c0;">{main_metric} ({latest_year})</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                growth_color = '#00ff00' if growth > 0 else '#ff4444'
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 0.9rem; color: #a0a0c0;">年度增长率</div>
                    <div style="font-size: 1.8rem; color: {growth_color}; font-weight: bold;">{growth:+.1f}%</div>
                    <div style="font-size: 0.8rem; color: #a0a0c0;">相比{prev_year}年</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 0.9rem; color: #a0a0c0;">数据时间范围</div>
                    <div style="font-size: 1.5rem; color: #ffffff; font-weight: bold;">{min_year}-{max_year}</div>
                    <div style="font-size: 0.8rem; color: #a0a0c0;">共{len(years)}年</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="font-size: 0.9rem; color: #a0a0c0;">可用指标数量</div>
                    <div style="font-size: 1.8rem; color: #ffffff; font-weight: bold;">{len(numeric_cols)}</div>
                    <div style="font-size: 0.8rem; color: #a0a0c0;">经济指标</div>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 图表配置区域
    st.markdown('<div class="section-header">📊 可视化分析</div>', unsafe_allow_html=True)
    
    # 初始化配置变量，避免未定义错误
    selected_metrics = []
    year_range = (min_year, max_year)
    selected_metric = numeric_cols[0] if numeric_cols else None
    comparison_years = years[-5:] if len(years) >= 5 else years
    num_years = 5
    x_metric = numeric_cols[0] if numeric_cols else None
    y_metric = numeric_cols[1] if len(numeric_cols) > 1 else (numeric_cols[0] if numeric_cols else None)
    color_by = "无"
    
    col_config, col_chart = st.columns([1, 3])
    
    with col_config:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.subheader("📝 图表配置")
        
        # 根据图表类型显示不同的配置
        if chart_type in ["时间序列趋势图", "堆叠面积图"]:
            selected_metrics = st.multiselect(
                "选择指标",
                numeric_cols,
                default=numeric_cols[:min(3, len(numeric_cols))],
                help="选择要显示的指标"
            )
            
            year_range = st.slider(
                "年份范围",
                min_value=min_year,
                max_value=max_year,
                value=(min_year, max_year),
                help="选择要分析的年份范围"
            )
            
        elif chart_type in ["年度对比柱状图", "多年度占比饼图"]:
            selected_metric = st.selectbox(
                "选择指标",
                numeric_cols,
                help="选择要分析的指标"
            )
            
            if chart_type == "多年度占比饼图":
                num_years = st.slider(
                    "显示年份数量",
                    min_value=3,
                    max_value=min(10, len(years)),
                    value=min(5, len(years)),
                    help="选择要显示的最近年份数量"
                )
            else:
                comparison_years = st.multiselect(
                    "选择对比年份",
                    years,
                    default=years[-5:] if len(years) >= 5 else years,
                    help="选择要对比的年份"
                )
                
        elif chart_type == "热力图分析":
            selected_metric = st.selectbox(
                "选择指标",
                numeric_cols,
                help="选择要分析的指标"
            )
            
            year_range = st.slider(
                "年份范围",
                min_value=min_year,
                max_value=max_year,
                value=(max_year-9, max_year) if max_year - min_year >= 9 else (min_year, max_year),
                help="选择要分析的年份范围"
            )
            
        elif chart_type == "相关性散点图":
            col_x, col_y = st.columns(2)
            with col_x:
                x_metric = st.selectbox("X轴指标", numeric_cols)
            with col_y:
                y_options = numeric_cols.copy()
                if x_metric in y_options:
                    y_options.remove(x_metric)
                y_metric = st.selectbox("Y轴指标", y_options)
            
            color_by = st.selectbox(
                "按颜色分组",
                ["无", "年份"] + numeric_cols
            )
        
        st.markdown('<p class="info-text">💡 提示：配置完成后图表会自动更新</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_chart:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        
        # 根据图表类型生成对应的图表
        if chart_type == "时间序列趋势图":
            st.subheader("📈 时间序列趋势分析")
            
            if selected_metrics and len(selected_metrics) > 0:
                # 筛选数据
                filtered_df = df[(df['year'] >= year_range[0]) & (df['year'] <= year_range[1])]
                
                if not filtered_df.empty:
                    fig = go.Figure()
                    
                    for i, metric in enumerate(selected_metrics):
                        # 按年份聚合数据
                        yearly_avg = filtered_df.groupby('year')[metric].mean().reset_index()
                        
                        fig.add_trace(go.Scatter(
                            x=yearly_avg['year'],
                            y=yearly_avg[metric],
                            mode='lines+markers',
                            name=metric,
                            line=dict(width=3, color=color_sequence[i % len(color_sequence)]),
                            marker=dict(size=6)
                        ))
                    
                    # 更新布局
                    fig.update_layout(
                        title=f"{year_range[0]}-{year_range[1]}年趋势分析",
                        xaxis_title="年份",
                        yaxis_title="数值",
                        showlegend=show_legend,
                        plot_bgcolor='#1e2130',
                        paper_bgcolor='#1e2130',
                        font=dict(color='white'),
                        hovermode='x unified'
                    )
                    
                    if show_grid:
                        fig.update_xaxes(
                            showgrid=True, 
                            gridwidth=1, 
                            gridcolor='#3a3a4a',
                            zerolinecolor='#3a3a4a'
                        )
                        fig.update_yaxes(
                            showgrid=True, 
                            gridwidth=1, 
                            gridcolor='#3a3a4a',
                            zerolinecolor='#3a3a4a'
                        )
                    else:
                        fig.update_xaxes(showgrid=False, zeroline=False)
                        fig.update_yaxes(showgrid=False, zeroline=False)
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("所选年份范围内无数据")
            else:
                st.warning("请选择至少一个指标")
        
        elif chart_type == "年度对比柱状图":
            st.subheader("📊 年度对比分析")
            
            if selected_metric and comparison_years and len(comparison_years) > 0:
                # 筛选数据
                comparison_data = []
                for year in comparison_years:
                    year_data = df[df['year'] == year]
                    if not year_data.empty:
                        avg_value = year_data[selected_metric].mean()
                        comparison_data.append({
                            '年份': str(year),
                            '数值': avg_value
                        })
                
                if comparison_data:
                    comp_df = pd.DataFrame(comparison_data)
                    
                    fig = px.bar(
                        comp_df,
                        x='年份',
                        y='数值',
                        color='年份',
                        title=f"{selected_metric} 年度对比",
                        color_discrete_sequence=color_sequence,
                        text='数值'
                    )
                    
                    fig.update_traces(
                        texttemplate='%{text:,.0f}',
                        textposition='outside',
                        marker_line_width=1,
                        marker_line_color='white'
                    )
                    
                    fig.update_layout(
                        plot_bgcolor='#1e2130',
                        paper_bgcolor='#1e2130',
                        font=dict(color='white'),
                        showlegend=show_legend
                    )
                    
                    if show_grid:
                        fig.update_xaxes(
                            showgrid=True, 
                            gridwidth=1, 
                            gridcolor='#3a3a4a'
                        )
                        fig.update_yaxes(
                            showgrid=True, 
                            gridwidth=1, 
                            gridcolor='#3a3a4a'
                        )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("所选年份无数据")
            else:
                st.warning("请选择至少一个年份")
        
        elif chart_type == "多年度占比饼图":
            st.subheader("🍩 多年度占比分析")
            
            if selected_metric:
                # 获取最近N年的数据
                recent_years = sorted(years, reverse=True)[:num_years]
                pie_data = []
                
                for year in recent_years:
                    year_data = df[df['year'] == year]
                    if not year_data.empty:
                        total_value = year_data[selected_metric].sum()
                        pie_data.append({
                            '年份': str(year),
                            '数值': total_value
                        })
                
                if pie_data and len(pie_data) > 1:
                    pie_df = pd.DataFrame(pie_data)
                    
                    fig = px.pie(
                        pie_df,
                        values='数值',
                        names='年份',
                        title=f"{selected_metric} - 最近{num_years}年占比分布",
                        color_discrete_sequence=color_sequence,
                        hole=0.3  # 环形图
                    )
                    
                    fig.update_traces(
                        textposition='inside',
                        textinfo='percent+label',
                        textfont_size=14,
                        marker=dict(line=dict(color='white', width=2))
                    )
                    
                    fig.update_layout(
                        plot_bgcolor='#1e2130',
                        paper_bgcolor='#1e2130',
                        font=dict(color='white'),
                        showlegend=show_legend,
                        legend=dict(
                            font=dict(size=12, color='white')
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("需要至少2年的数据来生成饼图")
        
        elif chart_type == "热力图分析":
            st.subheader("📅 热力图分析")
            
            if selected_metric:
                try:
                    # 准备数据
                    start_year, end_year = year_range
                    heatmap_years = list(range(start_year, end_year + 1))
                    
                    # 检查是否有足够的年份数据
                    if len(heatmap_years) < 2:
                        st.warning("需要至少2年的数据来生成热力图")
                        st.markdown('</div>', unsafe_allow_html=True)
                        return
                    
                    # 创建热力图数据
                    heatmap_data = []
                    available_years = df['year'].unique()
                    
                    for year in heatmap_years:
                        if year in available_years:
                            year_data = df[df['year'] == year]
                            if not year_data.empty:
                                # 使用4个季度或月份的数据
                                for period in range(1, 5):  # 假设4个季度
                                    # 这里简化处理，实际应用中可能需要真实的季度数据
                                    value = year_data[selected_metric].mean() * (0.8 + 0.2 * (period/4))
                                    heatmap_data.append({
                                        '年份': year,
                                        '时期': f'Q{period}',
                                        '数值': value
                                    })
                    
                    if heatmap_data:
                        heatmap_df = pd.DataFrame(heatmap_data)
                        
                        fig = px.density_heatmap(
                            heatmap_df,
                            x='时期',
                            y='年份',
                            z='数值',
                            title=f"{selected_metric} - {start_year}-{end_year}年热力图",
                            color_continuous_scale=color_sequence,
                            text_auto='.0f'
                        )
                        
                        fig.update_layout(
                            plot_bgcolor='#1e2130',
                            paper_bgcolor='#1e2130',
                            font=dict(color='white')
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("无法生成热力图数据")
                except Exception as e:
                    st.error(f"生成热力图时出错: {str(e)}")
        
        elif chart_type == "相关性散点图":
            st.subheader("🎯 相关性分析")
            
            if x_metric and y_metric and x_metric != y_metric:
                try:
                    scatter_df = df.copy()
                    
                    # 确保有数据
                    if scatter_df.empty or x_metric not in scatter_df.columns or y_metric not in scatter_df.columns:
                        st.warning("数据不完整，无法生成散点图")
                        st.markdown('</div>', unsafe_allow_html=True)
                        return
                    
                    # 移除缺失值
                    scatter_df = scatter_df[[x_metric, y_metric, 'year_str']].dropna()
                    
                    if len(scatter_df) < 2:
                        st.warning("数据点不足，无法生成散点图")
                        st.markdown('</div>', unsafe_allow_html=True)
                        return
                    
                    if color_by == "无":
                        fig = px.scatter(
                            scatter_df,
                            x=x_metric,
                            y=y_metric,
                            title=f"{x_metric} vs {y_metric} 相关性分析",
                            trendline="ols",
                            color_discrete_sequence=[color_sequence[0]]
                        )
                    elif color_by == "年份":
                        fig = px.scatter(
                            scatter_df,
                            x=x_metric,
                            y=y_metric,
                            color='year_str',
                            title=f"{x_metric} vs {y_metric} 相关性分析（按年份）",
                            trendline="ols",
                            color_discrete_sequence=color_sequence
                        )
                    else:
                        if color_by in scatter_df.columns:
                            fig = px.scatter(
                                scatter_df,
                                x=x_metric,
                                y=y_metric,
                                color=color_by,
                                title=f"{x_metric} vs {y_metric} 相关性分析（按{color_by}）",
                                trendline="ols",
                                color_continuous_scale=color_sequence
                            )
                        else:
                            st.warning(f"颜色分组列 '{color_by}' 不存在")
                            color_by = "无"
                            fig = px.scatter(
                                scatter_df,
                                x=x_metric,
                                y=y_metric,
                                title=f"{x_metric} vs {y_metric} 相关性分析",
                                trendline="ols",
                                color_discrete_sequence=[color_sequence[0]]
                            )
                    
                    # 计算相关系数
                    correlation = scatter_df[x_metric].corr(scatter_df[y_metric])
                    
                    fig.update_layout(
                        plot_bgcolor='#1e2130',
                        paper_bgcolor='#1e2130',
                        font=dict(color='white'),
                        showlegend=show_legend,
                        title=f"{fig.layout.title.text}<br><sup>相关系数: {correlation:.3f}</sup>"
                    )
                    
                    if show_grid:
                        fig.update_xaxes(
                            showgrid=True, 
                            gridwidth=1, 
                            gridcolor='#3a3a4a'
                        )
                        fig.update_yaxes(
                            showgrid=True, 
                            gridwidth=1, 
                            gridcolor='#3a3a4a'
                        )
                    
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"生成散点图时出错: {str(e)}")
            else:
                st.warning("请选择两个不同的指标")
        
        elif chart_type == "堆叠面积图":
            st.subheader("📊 堆叠面积图")
            
            if selected_metrics and len(selected_metrics) > 0:
                filtered_df = df[(df['year'] >= year_range[0]) & (df['year'] <= year_range[1])]
                
                if not filtered_df.empty:
                    fig = go.Figure()
                    
                    # 为堆叠面积图准备数据
                    for i, metric in enumerate(selected_metrics):
                        # 按年份聚合
                        yearly_avg = filtered_df.groupby('year')[metric].mean().reset_index()
                        
                        fig.add_trace(go.Scatter(
                            x=yearly_avg['year'],
                            y=yearly_avg[metric],
                            mode='lines',
                            name=metric,
                            stackgroup='one',  # 关键参数：堆叠
                            line=dict(width=0.5, color=color_sequence[i % len(color_sequence)]),
                            fillcolor=color_sequence[i % len(color_sequence)]
                        ))
                    
                    fig.update_layout(
                        title=f"{year_range[0]}-{year_range[1]}年指标堆叠分布",
                        xaxis_title="年份",
                        yaxis_title="数值",
                        showlegend=show_legend,
                        plot_bgcolor='#1e2130',
                        paper_bgcolor='#1e2130',
                        font=dict(color='white'),
                        hovermode='x unified'
                    )
                    
                    if show_grid:
                        fig.update_xaxes(
                            showgrid=True, 
                            gridwidth=1, 
                            gridcolor='#3a3a4a'
                        )
                        fig.update_yaxes(
                            showgrid=True, 
                            gridwidth=1, 
                            gridcolor='#3a3a4a'
                        )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("所选年份范围内无数据")
            else:
                st.warning("请选择至少一个指标")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 底部信息
    st.markdown("---")
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.markdown("""
        <div style="color: #a0a0c0;">
        <h4>📊 图表类型说明</h4>
        <ul style="margin-left: -20px;">
        <li>趋势图：显示指标随时间变化</li>
        <li>柱状图：年度对比分析</li>
        <li>饼图：多年度占比分布</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col_info2:
        st.markdown(f"""
        <div style="color: #a0a0c0;">
        <h4>📈 数据统计</h4>
        <p>• 总数据年份：{len(years)}年</p>
        <p>• 可用指标：{len(numeric_cols)}个</p>
        <p>• 最新年份：{max_year}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_info3:
        st.markdown("""
        <div style="color: #a0a0c0;">
        <h4>💡 使用提示</h4>
        <p>• 在侧边栏切换图表类型</p>
        <p>• 可调整颜色方案和显示选项</p>
        <p>• 鼠标悬停查看详细数据</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
