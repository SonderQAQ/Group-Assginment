import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime

def main():
    st.set_page_config(page_title="马来西亚GDP数据分析", layout="wide")
    
    st.title("📊 马来西亚GDP数据分析")
    st.write("数据来源：马来西亚统计局 (Department of Statistics Malaysia)")
    
    # 加载数据
    @st.cache_data
    def load_data():
        URL_DATA = 'https://storage.dosm.gov.my/gdp/gdp_annual_nominal_supply.parquet'
        df = pd.read_parquet(URL_DATA)
        
        # 修复日期列 - 处理纳秒级时间戳
        if 'date' in df.columns: 
            # 方法1: 转换为datetime并去掉纳秒部分
            df['date'] = pd.to_datetime(df['date']).dt.floor('s')  # 去掉纳秒，保留到秒
            
            # 方法2: 或者转换为字符串格式显示
            df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')
            
        return df
    
    try:
        df = load_data()
        
        st.success(f"✅ 数据加载成功！共 {len(df)} 行数据")
        
        # 使用tabs组织内容
        tab1, tab2, tab3, tab4 = st.tabs(["📋 数据预览", "📊 数据分析", "📈 可视化", "💾 数据下载"])
        
        with tab1:
            st.subheader("完整数据预览")
            
            # 显示列信息
            st.write("**数据列:**")
            cols = st.columns(4)
            for i, col in enumerate(df.columns):
                cols[i % 4].write(f"• {col} ({df[col].dtype})")
            
            # 搜索和筛选
            st.subheader("数据搜索和筛选")
            search_term = st.text_input("搜索关键词（在日期列中搜索）:", placeholder="例如: 2020, Q1, 等")
            
            if search_term:
                mask = df.apply(lambda row: row.astype(str).str.contains(search_term, case=False, na=False).any(), axis=1)
                filtered_df = df[mask]
                st.write(f"找到 {len(filtered_df)} 条匹配记录")
                st.dataframe(filtered_df, use_container_width=True)
            else:
                # 分页显示数据
                page_size = st.slider("每页显示行数:", min_value=10, max_value=100, value=20)
                total_pages = max(1, len(df) // page_size)
                page = st.number_input("页码:", min_value=1, max_value=total_pages, value=1)
                
                start_idx = (page - 1) * page_size
                end_idx = min(start_idx + page_size, len(df))
                
                st.write(f"显示第 {start_idx + 1} 到 {end_idx} 行 (共 {len(df)} 行)")
                st.dataframe(df.iloc[start_idx:end_idx], use_container_width=True)
        
        with tab2:
            st.subheader("数据统计信息")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**数据基本信息:**")
                st.metric("总行数", len(df))
                st.metric("总列数", len(df.columns))
                
                # 显示数据类型分布
                st.write("**数据类型分布:**")
                dtype_counts = df.dtypes.value_counts()
                for dtype, count in dtype_counts.items():
                    st.write(f"- {dtype}: {count}")
            
            with col2:
                st.write("**缺失值统计:**")
                missing_df = df.isnull().sum().reset_index()
                missing_df.columns = ['列名', '缺失值数量']
                missing_df = missing_df[missing_df['缺失值数量'] > 0]
                
                if len(missing_df) > 0:
                    st.dataframe(missing_df, use_container_width=True)
                else:
                    st.success("✅ 没有缺失值")
            
            # 数值列统计
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                st.subheader("数值列统计摘要")
                st.dataframe(df[numeric_cols].describe(), use_container_width=True)
            
            # 日期列信息
            date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
            if date_cols:
                st.subheader("日期列信息")
                for date_col in date_cols:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**{date_col}**:")
                        st.write(f"- 最早: {df[date_col].min().date()}")
                        st.write(f"- 最晚: {df[date_col].max().date()}")
                        st.write(f"- 唯一值数量: {df[date_col].nunique()}")
        
        with tab3:
            st.subheader("数据可视化")
            
            # 检查是否有数值列可以绘图
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if numeric_cols and 'date' in df.columns:
                st.write("**时间序列图**")
                
                selected_col = st.selectbox("选择要可视化的数值列:", numeric_cols)
                
                if selected_col:
                    # 按日期排序
                    plot_df = df.sort_values('date')
                    
                    # 创建简单的折线图
                    st.line_chart(
                        plot_df.set_index('date')[selected_col],
                        use_container_width=True
                    )
                    
                    # 显示统计数据
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(f"{selected_col} 平均值", f"{plot_df[selected_col].mean():,.2f}")
                    with col2:
                        st.metric(f"{selected_col} 中位数", f"{plot_df[selected_col].median():,.2f}")
                    with col3:
                        st.metric(f"{selected_col} 总和", f"{plot_df[selected_col].sum():,.2f}")
            else:
                st.info("没有足够的数据进行可视化（需要日期列和数值列）")
        
        with tab4:
            st.subheader("数据下载")
            
            st.write("**下载选项:**")
            
            # 下载完整数据
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 下载完整数据 (CSV)",
                data=csv,
                file_name="malaysia_gdp_full_data.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            # 下载处理后的数据（不含纳秒时间戳）
            if 'date_str' in df.columns:
                clean_df = df.copy()
                clean_csv = clean_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 下载简化数据 (CSV，日期格式简化)",
                    data=clean_csv,
                    file_name="malaysia_gdp_simplified.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            st.divider()
            
            # 数据预览
            st.write("**数据预览（前10行）:**")
            st.dataframe(df.head(10), use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ 加载数据时出错: {str(e)}")
        st.info("💡 请检查网络连接或稍后重试")
        
        # 显示错误详情用于调试
        with st.expander("调试信息"):
            st.code(f"错误类型: {type(e).__name__}")
            st.code(f"错误信息: {str(e)}")

if __name__ == "__main__":
    main()

#streamlit run [file.name].py
