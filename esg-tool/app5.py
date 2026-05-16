# 导入核心依赖
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy.optimize import minimize
import dashscope
from datetime import datetime

# -------------------------- 全局配置 --------------------------
# 页面配置（改标题和图标）
st.set_page_config(
    page_title="苏ESG - 苏州企业ESG分析平台",
    page_icon="🌱",
    layout="wide"
)

# 通义千问API配置（替换成你自己的API Key！）
# 申请地址：https://dashscope.console.aliyun.com/
dashscope.api_key = "OS-r29as9jl15bhvux0"  # 这里改成你的API Key

# -------------------------- 数据加载 --------------------------
# 加载苏州企业ESG数据（从CSV加载，不再硬编码）
@st.cache_data  # 缓存数据，提升加载速度
def load_esg_data():
        # 读取CSV文件
       import os
       import pandas as pd
       import streamlit as st

BASE_DIR = os.path.dirname(__file__)
file_path = os.path.join(BASE_DIR, "data", "suzhou_esg_data.csv")
 df = pd.read_csv(file_path)
        # 计算综合ESG得分（权重：E=30%, S=30%, G=40%）
        df["综合ESG"] = (df["E得分"]*0.3 + df["S得分"]*0.3 + df["G得分"]*0.4).round(1)
        # 计算各行业平均ESG得分（用于对比）
        industry_avg = df.groupby("行业")[["E得分", "S得分", "G得分", "综合ESG"]].mean().round(1)
        return df, industry_avg
    except FileNotFoundError:
        st.error("❌ 找不到数据文件！请检查data/suzhou_esg_data.csv是否存在")
        st.stop()
    except Exception as e:
        st.error(f"❌ 数据加载失败：{str(e)}")
        st.stop()

# 初始化数据
stock_df, industry_avg = load_esg_data()

# -------------------------- 页面标题 --------------------------
st.title("🌱 苏ESG - 苏州本土企业ESG量化分析与智能投研平台")
st.divider()

# -------------------------- 1. ESG综合评分计算器 --------------------------
st.subheader("📊 ESG综合评分计算器")
with st.expander("点击展开评分功能", expanded=True):
    # 分栏布局
    col1, col2 = st.columns(2)
    
    with col1:
        # 用户输入ESG得分
        st.write("### 输入企业ESG得分（0-100）")
        e_score = st.number_input("环境(E)得分", min_value=0, max_value=100, value=75, step=1)
        s_score = st.number_input("社会(S)得分", min_value=0, max_value=100, value=70, step=1)
        g_score = st.number_input("治理(G)得分", min_value=0, max_value=100, value=80, step=1)
        
        # 用户自定义权重（自动归一化）
        st.write("### 自定义权重（总和自动归一化）")
        e_weight = st.number_input("E权重(%)", min_value=0, max_value=100, value=30, step=1)
        s_weight = st.number_input("S权重(%)", min_value=0, max_value=100, value=30, step=1)
        g_weight = st.number_input("G权重(%)", min_value=0, max_value=100, value=40, step=1)
        
        # 权重归一化（解决用户输入总和不为100的问题）
        total_weight = e_weight + s_weight + g_weight
        if total_weight != 100:
            e_weight = (e_weight / total_weight) * 100
            s_weight = (s_weight / total_weight) * 100
            g_weight = (g_weight / total_weight) * 100
            st.info(f"✅ 权重已自动归一化：E={e_weight:.1f}%, S={s_weight:.1f}%, G={g_weight:.1f}%")
        
        # 选择所属行业（用于对比）
        selected_industry = st.selectbox("选择企业所属行业", options=industry_avg.index.tolist())
    
    with col2:
        # 计算综合得分
        esg_score = (e_score * e_weight/100) + (s_score * s_weight/100) + (g_score * g_weight/100)
        esg_score = round(esg_score, 1)
        
        # 评级规则
        def get_rating(score):
            if score >= 90:
                return "AAA（优秀）"
            elif score >= 80:
                return "AA（良好）"
            elif score >= 70:
                return "A（合格）"
            elif score >= 60:
                return "BBB（待改进）"
            else:
                return "BB（不合格）"
        
        rating = get_rating(esg_score)
        
        # 对比行业平均
        industry_e = industry_avg.loc[selected_industry, "E得分"]
        industry_s = industry_avg.loc[selected_industry, "S得分"]
        industry_g = industry_avg.loc[selected_industry, "G得分"]
        industry_total = industry_avg.loc[selected_industry, "综合ESG"]
        diff = esg_score - industry_total
        
        # 展示结果
        st.write("### 测评结果")
        st.metric("综合ESG得分", f"{esg_score}/100", f"{diff:+.1f}（对比行业平均）")
        st.write(f"🏆 评级：{rating}")
        
        # 行业对比雷达图
        st.write("### 与行业平均对比")
        radar_df = pd.DataFrame({
            "维度": ["环境(E)", "社会(S)", "治理(G)"],
            "你的企业": [e_score, s_score, g_score],
            "行业平均": [industry_e, industry_s, industry_g]
        })
        
        fig = px.line_polar(radar_df, r="你的企业", theta="维度", line_close=True, name="你的企业")
        fig.add_trace(go.Scatterpolar(
            r=radar_df["行业平均"],
            theta=radar_df["维度"],
            line_close=True,
            name="行业平均"
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    
    # -------------------------- 报告导出功能 --------------------------
    st.divider()
    st.write("### 📥 导出测评报告")
    # 生成报告内容
    report_content = f"""
==================== 苏州企业ESG测评报告 ====================
测评时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
企业基本信息：
- 所属行业：{selected_industry}
- 自定义权重：E={e_weight:.1f}%, S={s_weight:.1f}%, G={g_weight:.1f}%

ESG得分详情：
- 环境(E)得分：{e_score}（行业平均：{industry_e}）
- 社会(S)得分：{s_score}（行业平均：{industry_s}）
- 治理(G)得分：{g_score}（行业平均：{g_score}）
- 综合ESG得分：{esg_score}/100（行业平均：{industry_total}）
- 评级：{rating}

对比分析：
- 你的企业综合ESG得分{diff:+.1f}分于{selected_industry}行业平均水平
- 优势维度：{max(["环境(E)", "社会(S)", "治理(G)"], key=lambda x: [e_score, s_score, g_score][["环境(E)", "社会(S)", "治理(G)"].index(x)])}
- 待改进维度：{min(["环境(E)", "社会(S)", "治理(G)"], key=lambda x: [e_score, s_score, g_score][["环境(E)", "社会(S)", "治理(G)"].index(x)])}

------------------------------------------------------------
本报告由「苏ESG」平台生成，仅供参考。
苏州绿色金融政策适配建议：可关注苏州市工业企业节能改造补贴、绿色贷款贴息等政策。
"""
    # 下载按钮
    st.download_button(
        label="点击下载ESG测评报告（TXT格式）",
        data=report_content,
        file_name=f"苏州ESG测评报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
        type="primary"
    )

# -------------------------- 2. AI智能优化建议 --------------------------
st.divider()
st.subheader("🤖 AI智能优化建议（贴合苏州政策）")
with st.expander("点击生成个性化建议", expanded=False):
    if st.button("生成苏州本地优化建议", type="primary"):
        with st.spinner("AI正在分析苏州政策并生成建议..."):
            # 构建提示词（重点贴合苏州政策）
            prompt = f"""
            你是苏州ESG领域的专家，现在需要给一家苏州{selected_industry}行业的企业提供ESG优化建议。
            企业ESG得分：环境(E)={e_score}, 社会(S)={s_score}, 治理(G)={g_score}。
            该行业苏州平均得分：E={industry_e}, S={industry_s}, G={industry_g}。
            
            要求：
            1. 生成3条具体、可落地的优化建议，每条建议必须贴合苏州本地政策（比如苏州节能补贴、绿色贷款、社保补贴、工业园区ESG试点等）；
            2. 建议要具体，不要空泛（比如“申请苏州工业园区ESG专项补贴”而不是“提升E得分”）；
            3. 语言简洁，每条建议不超过50字；
            4. 优先针对得分低于行业平均的维度给出建议。
            """
            
            try:
                # 调用通义千问API
                response = dashscope.Generation.call(
                    model="qwen-turbo",  # 免费的轻量模型
                    prompt=prompt,
                    result_format="text",
                    temperature=0.7,  # 控制随机性
                    top_p=0.8
                )
                
                # 展示结果
                st.success("✅ AI优化建议生成完成！")
                st.write(response.output.text)
            except Exception as e:
                st.error(f"❌ AI建议生成失败：{str(e)}")
                st.info("💡 请检查你的通义千问API Key是否正确，或稍后重试")

# -------------------------- 3. ESG与财务相关性分析 --------------------------
st.divider()
st.subheader("📈 ESG与财务指标相关性分析")
with st.expander("点击查看分析结果", expanded=False):
    # 计算相关性
    corr_esg_return = round(stock_df["综合ESG"].corr(stock_df["预期收益率"]), 3)
    corr_esg_vol = round(stock_df["综合ESG"].corr(stock_df["波动率"]), 3)
    
    # 展示相关性结果
    col1, col2 = st.columns(2)
    with col1:
        st.metric("ESG与预期收益率相关性", corr_esg_return)
        if corr_esg_return > 0:
            st.write("✅ ESG得分越高，预期收益率越高")
        else:
            st.write("⚠️ ESG得分与预期收益率呈负相关")
    
    with col2:
        st.metric("ESG与波动率相关性", corr_esg_vol)
        if corr_esg_vol < 0:
            st.write("✅ ESG得分越高，风险越低")
        else:
            st.write("⚠️ ESG得分与风险呈正相关")
    
    # 可视化相关性
    fig1 = px.scatter(stock_df, x="综合ESG", y="预期收益率", 
                     title="ESG得分 vs 预期收益率",
                     trendline="ols",  # 加趋势线
                     hover_data=["公司名称", "行业"])
    fig2 = px.scatter(stock_df, x="综合ESG", y="波动率", 
                     title="ESG得分 vs 波动率",
                     trendline="ols",
                     hover_data=["公司名称", "行业"])
    
    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)

# -------------------------- 4. ESG约束下的投资组合优化 --------------------------
st.divider()
st.subheader("🎯 ESG约束下的投资组合优化（马科维茨模型）")
with st.expander("点击使用优化功能", expanded=False):
    # 选择行业
    target_industry = st.selectbox("选择投资行业", options=["全部"] + industry_avg.index.tolist())
    
    # 筛选数据
    if target_industry != "全部":
        portfolio_df = stock_df[stock_df["行业"] == target_industry].copy()
    else:
        portfolio_df = stock_df.copy()
    
    if len(portfolio_df) < 5:
        st.warning(f"⚠️ 所选行业只有{len(portfolio_df)}家企业，建议选择“全部”")
    
    # 定义优化目标（最小化风险，约束ESG得分和收益率）
    def portfolio_volatility(weights):
        returns = portfolio_df["预期收益率"].values
        cov_matrix = np.cov(returns)
        return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    
    # 约束条件
    esg_threshold = st.slider("最低综合ESG得分要求", min_value=60.0, max_value=90.0, value=75.0, step=0.1)
    return_threshold = st.slider("最低预期收益率要求", min_value=0.05, max_value=0.20, value=0.10, step=0.01)
    
    # 约束列表
    constraints = [
        {"type": "eq", "fun": lambda x: np.sum(x) - 1},  # 权重和为1
        {"type": "ineq", "fun": lambda x: np.dot(x, portfolio_df["预期收益率"].values) - return_threshold},  # 收益率≥阈值
        {"type": "ineq", "fun": lambda x: np.dot(x, portfolio_df["综合ESG"].values) - esg_threshold}  # ESG≥阈值
    ]
    
    # 权重边界（0-1）
    bounds = tuple((0, 1) for _ in range(len(portfolio_df)))
    
    # 初始权重
    init_weights = np.ones(len(portfolio_df)) / len(portfolio_df)
    
    # 执行优化
    if st.button("开始优化投资组合", type="primary"):
        with st.spinner("正在优化..."):
            try:
                result = minimize(
                    portfolio_volatility,
                    init_weights,
                    method="SLSQP",
                    bounds=bounds,
                    constraints=constraints
                )
                
                if result.success:
                    # 提取优化结果
                    portfolio_df["优化权重"] = result.x.round(4)
                    portfolio_df["权重占比"] = (portfolio_df["优化权重"] * 100).round(2)
                    
                    # 筛选权重>0的企业
                    selected_stocks = portfolio_df[portfolio_df["优化权重"] > 0.0001].copy()
                    
                    # 计算组合指标
                    port_return = np.dot(selected_stocks["优化权重"], selected_stocks["预期收益率"]).round(4)
                    port_vol = portfolio_volatility(selected_stocks["优化权重"]).round(4)
                    port_esg = np.dot(selected_stocks["优化权重"], selected_stocks["综合ESG"]).round(1)
                    
                    # 展示结果
                    st.success("✅ 投资组合优化完成！")
                    st.write(f"📊 组合预期收益率：{port_return*100:.2f}% | 组合波动率：{port_vol*100:.2f}% | 组合ESG得分：{port_esg}")
                    
                    # 展示权重分布
                    st.write("### 最优权重分布")
                    fig = px.pie(selected_stocks, values="权重占比", names="公司名称", title="投资组合权重")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # 展示详细表格
                    st.write("### 详细持仓信息")
                    st.dataframe(selected_stocks[["公司名称", "行业", "综合ESG", "预期收益率", "波动率", "权重占比"]], use_container_width=True)
                else:
                    st.error(f"❌ 优化失败：{result.message}")
                    st.info("💡 建议降低ESG或收益率要求重试")
            except Exception as e:
                st.error(f"❌ 优化出错：{str(e)}")

# -------------------------- 页脚 --------------------------
st.divider()
st.write("""
📞 联系我们：xxx@xxx.com | 📍 苏州工业园区 | 🌱 助力苏州绿色金融发展
""")
