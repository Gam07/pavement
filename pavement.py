"""
AASHTO 1993 Pavement Design - Structural Number Calculator
สำหรับการออกแบบผิวทางยืดหยุ่น (Flexible Pavement)

Author: Civil Engineering Student
Date: 2026
"""

import streamlit as st
import numpy as np
import pandas as pd
from scipy.optimize import fsolve
import math

# Try to import plotly, but make it optional
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("⚠️ Plotly not installed. Some visualizations will be limited. Install with: pip install plotly")

# ================================
# ฟังก์ชันคำนวณหลัก
# ================================

def calculate_sn_from_aashto(W18, ZR, So, delta_psi, MR):
    """
    คำนวณ Structural Number (SN) จากสมการ AASHTO 1993
    
    Parameters:
    - W18: Predicted 18-kip ESAL (Equivalent Single Axle Load)
    - ZR: Standard normal deviate (reliability)
    - So: Combined standard error
    - delta_psi: Design serviceability loss (PSI)
    - MR: Resilient modulus of subgrade (psi)
    
    Returns:
    - SN: Structural Number
    """
    
    def aashto_equation(SN):
        """
        AASHTO 1993 Design Equation:
        log10(W18) = ZR*So + 9.36*log10(SN+1) - 0.20 + 
                     [log10(ΔPSI/(4.2-1.5))] / [0.40 + 1094/(SN+1)^5.19] + 
                     2.32*log10(MR) - 8.07
        """
        term1 = ZR * So
        term2 = 9.36 * np.log10(SN + 1)
        term3 = -0.20
        
        numerator = np.log10(delta_psi / (4.2 - 1.5))
        denominator = 0.40 + (1094 / ((SN + 1) ** 5.19))
        term4 = numerator / denominator
        
        term5 = 2.32 * np.log10(MR)
        term6 = -8.07
        
        return term1 + term2 + term3 + term4 + term5 + term6 - np.log10(W18)
    
    # แก้สมการหา SN
    SN_initial_guess = 3.0
    SN_solution = fsolve(aashto_equation, SN_initial_guess)[0]
    
    return max(SN_solution, 0)


def get_layer_coefficient(material_type, material_property):
    """
    คำนวณ Layer Coefficient (a) สำหรับชั้นวัสดุต่างๆ
    
    Parameters:
    - material_type: ประเภทชั้นวัสดุ ('asphalt', 'base', 'subbase')
    - material_property: คุณสมบัติวัสดุ (Elastic Modulus สำหรับ asphalt, CBR หรือ Resilient Modulus สำหรับ base/subbase)
    
    Returns:
    - a: Layer coefficient
    """
    
    if material_type == 'asphalt':
        # a1 = 0.44 สำหรับ asphalt concrete ทั่วไป
        # หรือคำนวณจาก Elastic Modulus
        EAC = material_property  # psi
        a1 = 0.44  # ค่ามาตรฐาน
        # สามารถปรับได้ตามคุณภาพ: a1 = 0.40-0.44 (good), 0.30-0.40 (fair), 0.20-0.30 (poor)
        return a1
    
    elif material_type == 'base':
        # Base course: crushed stone, gravel
        # a2 ขึ้นอับกับ Resilient Modulus หรือ CBR
        # ประมาณการ: a2 = 0.10-0.14 สำหรับ crushed stone
        a2 = 0.14  # ค่ามาตรฐานสำหรับ crushed stone คุณภาพดี
        return a2
    
    elif material_type == 'subbase':
        # Subbase course
        # a3 = 0.08-0.11
        a3 = 0.11  # ค่ามาตรฐาน
        return a3
    
    return 0.0


def calculate_layer_thickness(SN_required, a1, a2, a3, m2=1.0, m3=1.0):
    """
    คำนวณความหนาของแต่ละชั้น
    
    SN = a1*D1 + a2*D2*m2 + a3*D3*m3
    
    Parameters:
    - SN_required: Structural Number ที่ต้องการ
    - a1, a2, a3: Layer coefficients
    - m2, m3: Drainage coefficients
    
    Returns:
    - D1, D2, D3: ความหนาของแต่ละชั้น (inches)
    """
    
    # ใช้แนวทางการออกแบบทั่วไป
    # สมมติ D1 (asphalt) ขั้นต่ำ 3 นิ้ว
    D1_min = 3.0
    D2_min = 6.0
    D3_min = 6.0
    
    # คำนวณ SN ที่เหลือหลังจากชั้น asphalt
    SN1 = a1 * D1_min
    SN_remaining = SN_required - SN1
    
    if SN_remaining <= 0:
        return D1_min, 0, 0
    
    # คำนวณ SN ที่เหลือหลังจากชั้น base
    SN2 = a2 * D2_min * m2
    SN_remaining2 = SN_remaining - SN2
    
    if SN_remaining2 <= 0:
        return D1_min, D2_min, 0
    
    # คำนวณความหนาชั้น subbase
    D3 = SN_remaining2 / (a3 * m3)
    
    return D1_min, D2_min, D3


def get_reliability_z(reliability_percent):
    """
    แปลง Reliability (%) เป็น Standard Normal Deviate (ZR)
    """
    reliability_table = {
        50: 0.000,
        60: -0.253,
        70: -0.524,
        75: -0.674,
        80: -0.841,
        85: -1.037,
        90: -1.282,
        95: -1.645,
        99: -2.327,
        99.9: -3.090
    }
    return reliability_table.get(reliability_percent, -1.645)


# ================================
# Streamlit UI
# ================================

def main():
    st.set_page_config(
        page_title="AASHTO 1993 Pavement Design",
        page_icon="🛣️",
        layout="wide"
    )
    
    st.title("🛣️ AASHTO 1993 Flexible Pavement Design")
    st.markdown("### โปรแกรมคำนวณ Structural Number (SN) สำหรับผิวทางลาดยาง")
    
    st.markdown("---")
    
    # Sidebar สำหรับ input parameters
    with st.sidebar:
        st.header("📊 Input Parameters")
        
        st.subheader("1. Traffic Data")
        W18 = st.number_input(
            "W18 - 18-kip ESAL",
            min_value=1000.0,
            max_value=100000000.0,
            value=1000000.0,
            step=100000.0,
            format="%.0f",
            help="จำนวนรถบรรทุกเทียบเท่ามาตรฐาน 18,000 ปอนด์ ตลอดอายุการใช้งาน"
        )
        
        st.subheader("2. Reliability")
        reliability = st.selectbox(
            "Reliability (%)",
            options=[50, 60, 70, 75, 80, 85, 90, 95, 99, 99.9],
            index=6,  # default 90%
            help="ระดับความเชื่อมั่นในการออกแบบ"
        )
        ZR = get_reliability_z(reliability)
        st.info(f"ZR = {ZR:.3f}")
        
        So = st.number_input(
            "So - Standard Error",
            min_value=0.30,
            max_value=0.50,
            value=0.45,
            step=0.01,
            help="ค่าความคลาดเคลื่อนมาตรฐาน (ทั่วไปใช้ 0.40-0.50)"
        )
        
        st.subheader("3. Serviceability")
        p_initial = st.number_input(
            "Initial PSI (p₀)",
            min_value=3.0,
            max_value=5.0,
            value=4.2,
            step=0.1,
            help="ค่า serviceability เริ่มต้น"
        )
        
        p_terminal = st.number_input(
            "Terminal PSI (pₜ)",
            min_value=1.5,
            max_value=3.0,
            value=2.5,
            step=0.1,
            help="ค่า serviceability ปลายทาง"
        )
        
        delta_psi = p_initial - p_terminal
        st.info(f"ΔPSI = {delta_psi:.1f}")
        
        st.subheader("4. Subgrade Properties")
        MR = st.number_input(
            "MR - Resilient Modulus (psi)",
            min_value=1000.0,
            max_value=30000.0,
            value=10000.0,
            step=500.0,
            help="Resilient Modulus ของชั้นดินเดิม"
        )
        
        st.subheader("5. Layer Coefficients")
        a1 = st.slider(
            "a₁ - Asphalt Layer Coefficient",
            min_value=0.20,
            max_value=0.50,
            value=0.44,
            step=0.01,
            help="ค่าสัมประสิทธิ์ชั้นแอสฟัลต์ (0.40-0.44 สำหรับคุณภาพดี)"
        )
        
        a2 = st.slider(
            "a₂ - Base Layer Coefficient",
            min_value=0.05,
            max_value=0.20,
            value=0.14,
            step=0.01,
            help="ค่าสัมประสิทธิ์ชั้นฐานราก (0.12-0.14 สำหรับหินคลุก)"
        )
        
        a3 = st.slider(
            "a₃ - Subbase Layer Coefficient",
            min_value=0.05,
            max_value=0.15,
            value=0.11,
            step=0.01,
            help="ค่าสัมประสิทธิ์ชั้นรองฐาน"
        )
        
        st.subheader("6. Drainage Coefficients")
        m2 = st.slider(
            "m₂ - Base Drainage Coefficient",
            min_value=0.8,
            max_value=1.2,
            value=1.0,
            step=0.05,
            help="ค่าสัมประสิทธิ์การระบายน้ำชั้นฐานราก (1.0 = fair)"
        )
        
        m3 = st.slider(
            "m₃ - Subbase Drainage Coefficient",
            min_value=0.8,
            max_value=1.2,
            value=1.0,
            step=0.05,
            help="ค่าสัมประสิทธิ์การระบายน้ำชั้นรองฐาน"
        )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📈 Calculation Results")
        
        # คำนวณ SN
        try:
            SN_required = calculate_sn_from_aashto(W18, ZR, So, delta_psi, MR)
            
            st.success(f"### Required Structural Number (SN) = {SN_required:.2f}")
            
            # คำนวณความหนาชั้นต่างๆ
            D1, D2, D3 = calculate_layer_thickness(SN_required, a1, a2, a3, m2, m3)
            
            st.subheader("🏗️ Layer Thicknesses")
            
            # แสดงผลในรูปแบบตาราง
            layer_data = {
                "Layer": ["Asphalt Concrete (AC)", "Base Course", "Subbase"],
                "Coefficient (a)": [f"{a1:.2f}", f"{a2:.2f}", f"{a3:.2f}"],
                "Drainage (m)": ["1.00", f"{m2:.2f}", f"{m3:.2f}"],
                "Thickness (in)": [f"{D1:.1f}", f"{D2:.1f}", f"{D3:.1f}"],
                "Thickness (cm)": [f"{D1*2.54:.1f}", f"{D2*2.54:.1f}", f"{D3*2.54:.1f}"]
            }
            
            df_layers = pd.DataFrame(layer_data)
            st.dataframe(df_layers, use_container_width=True)
            
            # คำนวณ SN ของแต่ละชั้น
            SN1 = a1 * D1
            SN2 = a2 * D2 * m2
            SN3 = a3 * D3 * m3
            SN_total = SN1 + SN2 + SN3
            
            st.subheader("📊 Structural Number Contribution")
            contribution_data = {
                "Layer": ["Asphalt (SN₁)", "Base (SN₂)", "Subbase (SN₃)", "Total"],
                "SN Value": [f"{SN1:.2f}", f"{SN2:.2f}", f"{SN3:.2f}", f"{SN_total:.2f}"]
            }
            df_sn = pd.DataFrame(contribution_data)
            st.dataframe(df_sn, use_container_width=True)
            
            # Visualization - Layer thickness diagram
            st.subheader("📐 Pavement Cross-Section")
            
            if PLOTLY_AVAILABLE:
                fig_section = go.Figure()
                
                # วาดแต่ละชั้น
                y_top = 0
                colors = ['#2C3E50', '#95A5A6', '#BDC3C7']
                labels = [f'AC: {D1:.1f}" ({D1*2.54:.1f} cm)',
                         f'Base: {D2:.1f}" ({D2*2.54:.1f} cm)',
                         f'Subbase: {D3:.1f}" ({D3*2.54:.1f} cm)']
                thicknesses = [D1, D2, D3]
                
                for i, (thickness, color, label) in enumerate(zip(thicknesses, colors, labels)):
                    if thickness > 0:
                        fig_section.add_trace(go.Bar(
                            y=[label],
                            x=[thickness],
                            orientation='h',
                            marker=dict(color=color),
                            text=f"{thickness:.1f}\"",
                            textposition='inside',
                            name=label
                        ))
                
                fig_section.update_layout(
                    title="Pavement Layer Thickness",
                    xaxis_title="Thickness (inches)",
                    barmode='stack',
                    showlegend=False,
                    height=300
                )
                
                st.plotly_chart(fig_section, use_container_width=True)
            else:
                # Simple bar chart alternative using streamlit
                st.bar_chart({
                    'Asphalt': D1,
                    'Base': D2,
                    'Subbase': D3
                })
            
            # SN Contribution Pie Chart
            st.subheader("🥧 SN Contribution by Layer")
            
            if PLOTLY_AVAILABLE:
                fig_pie = go.Figure(data=[go.Pie(
                    labels=['Asphalt', 'Base', 'Subbase'],
                    values=[SN1, SN2, SN3],
                    hole=0.3,
                    marker=dict(colors=['#2C3E50', '#95A5A6', '#BDC3C7'])
                )])
                
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                # Alternative visualization
                contrib_df = pd.DataFrame({
                    'Layer': ['Asphalt', 'Base', 'Subbase'],
                    'SN Contribution': [SN1, SN2, SN3]
                })
                st.bar_chart(contrib_df.set_index('Layer'))
            
        except Exception as e:
            st.error(f"Error in calculation: {str(e)}")
            st.error("กรุณาตรวจสอบค่า input parameters")
    
    with col2:
        st.header("ℹ️ Design Summary")
        
        summary_data = {
            "Parameter": [
                "W18 (ESAL)",
                "Reliability (%)",
                "ZR",
                "So",
                "ΔPSI",
                "MR (psi)",
                "Required SN"
            ],
            "Value": [
                f"{W18:,.0f}",
                f"{reliability}",
                f"{ZR:.3f}",
                f"{So:.2f}",
                f"{delta_psi:.1f}",
                f"{MR:,.0f}",
                f"{SN_required:.2f}" if 'SN_required' in locals() else "N/A"
            ]
        }
        
        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        st.subheader("📋 Design Notes")
        st.info("""
        **AASHTO 1993 Method**
        
        - ใช้สำหรับผิวทางยืดหยุ่น
        - SN = Structural Number
        - W18 = 18-kip ESAL
        - MR = Resilient Modulus
        - ΔPSI = Loss of Serviceability
        
        **Typical Values:**
        - Reliability: 80-95%
        - ΔPSI: 1.5-2.0
        - MR: 3,000-15,000 psi
        """)
        
        st.markdown("---")
        
        # Export results
        st.subheader("💾 Export Results")
        
        if st.button("📄 Generate Report"):
            report = f"""
AASHTO 1993 PAVEMENT DESIGN REPORT
{'='*50}

INPUT PARAMETERS:
- W18 (ESAL): {W18:,.0f}
- Reliability: {reliability}%
- Standard Normal Deviate (ZR): {ZR:.3f}
- Standard Error (So): {So:.2f}
- Initial PSI: {p_initial:.1f}
- Terminal PSI: {p_terminal:.1f}
- ΔPSI: {delta_psi:.1f}
- Subgrade MR: {MR:,.0f} psi

LAYER COEFFICIENTS:
- a1 (Asphalt): {a1:.2f}
- a2 (Base): {a2:.2f}
- a3 (Subbase): {a3:.2f}

DRAINAGE COEFFICIENTS:
- m2 (Base): {m2:.2f}
- m3 (Subbase): {m3:.2f}

RESULTS:
- Required SN: {SN_required:.2f}

LAYER THICKNESSES:
- Asphalt Concrete: {D1:.1f} inches ({D1*2.54:.1f} cm)
- Base Course: {D2:.1f} inches ({D2*2.54:.1f} cm)
- Subbase: {D3:.1f} inches ({D3*2.54:.1f} cm)

STRUCTURAL NUMBERS:
- SN1 (Asphalt): {SN1:.2f}
- SN2 (Base): {SN2:.2f}
- SN3 (Subbase): {SN3:.2f}
- Total SN: {SN_total:.2f}

{'='*50}
Generated by AASHTO 1993 Pavement Design Calculator
            """
            
            st.download_button(
                label="Download Report",
                data=report,
                file_name="pavement_design_report.txt",
                mime="text/plain"
            )
    
    # Sensitivity Analysis Section
    st.markdown("---")
    st.header("🔍 Sensitivity Analysis")
    
    sensitivity_param = st.selectbox(
        "Select parameter for sensitivity analysis:",
        ["W18", "MR", "Reliability"]
    )
    
    if sensitivity_param == "W18":
        W18_range = np.logspace(np.log10(W18*0.5), np.log10(W18*2), 20)
        SN_values = [calculate_sn_from_aashto(w, ZR, So, delta_psi, MR) for w in W18_range]
        
        if PLOTLY_AVAILABLE:
            fig_sens = go.Figure()
            fig_sens.add_trace(go.Scatter(
                x=W18_range,
                y=SN_values,
                mode='lines+markers',
                name='SN vs W18'
            ))
            fig_sens.update_layout(
                title="Sensitivity: SN vs W18",
                xaxis_title="W18 (ESAL)",
                yaxis_title="Structural Number (SN)",
                xaxis_type="log"
            )
            st.plotly_chart(fig_sens, use_container_width=True)
        else:
            sens_df = pd.DataFrame({
                'W18': W18_range,
                'SN': SN_values
            })
            st.line_chart(sens_df.set_index('W18'))
        
    elif sensitivity_param == "MR":
        MR_range = np.linspace(MR*0.5, MR*1.5, 20)
        SN_values = [calculate_sn_from_aashto(W18, ZR, So, delta_psi, mr) for mr in MR_range]
        
        if PLOTLY_AVAILABLE:
            fig_sens = go.Figure()
            fig_sens.add_trace(go.Scatter(
                x=MR_range,
                y=SN_values,
                mode='lines+markers',
                name='SN vs MR'
            ))
            fig_sens.update_layout(
                title="Sensitivity: SN vs MR",
                xaxis_title="Resilient Modulus (psi)",
                yaxis_title="Structural Number (SN)"
            )
            st.plotly_chart(fig_sens, use_container_width=True)
        else:
            sens_df = pd.DataFrame({
                'MR': MR_range,
                'SN': SN_values
            })
            st.line_chart(sens_df.set_index('MR'))
        
    elif sensitivity_param == "Reliability":
        reliability_range = [50, 60, 70, 75, 80, 85, 90, 95, 99]
        ZR_range = [get_reliability_z(r) for r in reliability_range]
        SN_values = [calculate_sn_from_aashto(W18, zr, So, delta_psi, MR) for zr in ZR_range]
        
        if PLOTLY_AVAILABLE:
            fig_sens = go.Figure()
            fig_sens.add_trace(go.Scatter(
                x=reliability_range,
                y=SN_values,
                mode='lines+markers',
                name='SN vs Reliability'
            ))
            fig_sens.update_layout(
                title="Sensitivity: SN vs Reliability",
                xaxis_title="Reliability (%)",
                yaxis_title="Structural Number (SN)"
            )
            st.plotly_chart(fig_sens, use_container_width=True)
        else:
            sens_df = pd.DataFrame({
                'Reliability': reliability_range,
                'SN': SN_values
            })
            st.line_chart(sens_df.set_index('Reliability'))
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>AASHTO 1993 Flexible Pavement Design Calculator</p>
        <p>สำหรับการศึกษาและออกแบบเบื้องต้น - ควรตรวจสอบโดยวิศวกรผู้เชี่ยวชาญ</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
