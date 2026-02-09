"""
AASHTO 1993 Pavement Design - Structural Number Calculator (Minimal Version)
รองรับ Streamlit Cloud - ไม่ต้องใช้ external libraries

Author: Civil Engineering Student
"""

import streamlit as st
import math

# ================================
# ฟังก์ชันคำนวณหลัก
# ================================

def log10(x):
    """Calculate log base 10"""
    return math.log10(x)


def calculate_sn_from_aashto(W18, ZR, So, delta_psi, MR):
    """
    คำนวณ Structural Number (SN) จากสมการ AASHTO 1993
    ใช้ Newton-Raphson method
    """
    
    def aashto_equation(SN):
        """AASHTO 1993 Design Equation"""
        if SN <= 0:
            SN = 0.01
            
        term1 = ZR * So
        term2 = 9.36 * log10(SN + 1)
        term3 = -0.20
        
        numerator = log10(delta_psi / (4.2 - 1.5))
        denominator = 0.40 + (1094 / ((SN + 1) ** 5.19))
        term4 = numerator / denominator
        
        term5 = 2.32 * log10(MR)
        term6 = -8.07
        
        return term1 + term2 + term3 + term4 + term5 + term6 - log10(W18)
    
    def aashto_derivative(SN):
        """อนุพันธ์ของสมการ AASHTO"""
        if SN <= 0:
            SN = 0.01
            
        term1 = 9.36 / ((SN + 1) * math.log(10))
        
        numerator = log10(delta_psi / (4.2 - 1.5))
        denominator = 0.40 + (1094 / ((SN + 1) ** 5.19))
        d_denominator = -(1094 * 5.19 * ((SN + 1) ** -6.19))
        term2 = -numerator * d_denominator / (denominator ** 2)
        
        return term1 + term2
    
    # Newton-Raphson method
    SN = 3.0
    tolerance = 1e-6
    max_iterations = 100
    
    for i in range(max_iterations):
        f_SN = aashto_equation(SN)
        f_prime_SN = aashto_derivative(SN)
        
        if abs(f_prime_SN) < 1e-10:
            break
            
        SN_new = SN - f_SN / f_prime_SN
        
        if abs(SN_new - SN) < tolerance:
            return max(SN_new, 0)
        
        SN = max(SN_new, 0.01)
    
    return max(SN, 0)


def calculate_layer_thickness(SN_required, a1, a2, a3, m2=1.0, m3=1.0):
    """คำนวณความหนาของแต่ละชั้น"""
    D1_min = 3.0
    D2_min = 6.0
    
    SN1 = a1 * D1_min
    SN_remaining = SN_required - SN1
    
    if SN_remaining <= 0:
        return D1_min, 0, 0
    
    SN2 = a2 * D2_min * m2
    SN_remaining2 = SN_remaining - SN2
    
    if SN_remaining2 <= 0:
        return D1_min, D2_min, 0
    
    D3 = SN_remaining2 / (a3 * m3)
    
    return D1_min, D2_min, D3


def get_reliability_z(reliability_percent):
    """แปลง Reliability เป็น ZR"""
    reliability_table = {
        50: 0.000, 60: -0.253, 70: -0.524, 75: -0.674,
        80: -0.841, 85: -1.037, 90: -1.282, 95: -1.645,
        99: -2.327, 99.9: -3.090
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
    
    # Sidebar
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
            help="จำนวนรถบรรทุกเทียบเท่า 18,000 ปอนด์"
        )
        
        st.subheader("2. Reliability")
        reliability = st.selectbox(
            "Reliability (%)",
            options=[50, 60, 70, 75, 80, 85, 90, 95, 99, 99.9],
            index=6,
            help="ระดับความเชื่อมั่น"
        )
        ZR = get_reliability_z(reliability)
        st.info(f"ZR = {ZR:.3f}")
        
        So = st.number_input(
            "So - Standard Error",
            min_value=0.30,
            max_value=0.50,
            value=0.45,
            step=0.01
        )
        
        st.subheader("3. Serviceability")
        p_initial = st.number_input("Initial PSI (p₀)", 3.0, 5.0, 4.2, 0.1)
        p_terminal = st.number_input("Terminal PSI (pₜ)", 1.5, 3.0, 2.5, 0.1)
        delta_psi = p_initial - p_terminal
        st.info(f"ΔPSI = {delta_psi:.1f}")
        
        st.subheader("4. Subgrade Properties")
        MR = st.number_input(
            "MR - Resilient Modulus (psi)",
            1000.0, 30000.0, 10000.0, 500.0
        )
        
        st.subheader("5. Layer Coefficients")
        a1 = st.slider("a₁ - Asphalt", 0.20, 0.50, 0.44, 0.01)
        a2 = st.slider("a₂ - Base", 0.05, 0.20, 0.14, 0.01)
        a3 = st.slider("a₃ - Subbase", 0.05, 0.15, 0.11, 0.01)
        
        st.subheader("6. Drainage Coefficients")
        m2 = st.slider("m₂ - Base Drainage", 0.8, 1.2, 1.0, 0.05)
        m3 = st.slider("m₃ - Subbase Drainage", 0.8, 1.2, 1.0, 0.05)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📈 Calculation Results")
        
        try:
            SN_required = calculate_sn_from_aashto(W18, ZR, So, delta_psi, MR)
            st.success(f"### Required Structural Number (SN) = {SN_required:.2f}")
            
            D1, D2, D3 = calculate_layer_thickness(SN_required, a1, a2, a3, m2, m3)
            
            st.subheader("🏗️ Layer Thicknesses")
            
            # ตาราง
            st.markdown(f"""
            | Layer | Coefficient | Drainage | Thickness (in) | Thickness (cm) |
            |-------|------------|----------|----------------|----------------|
            | Asphalt Concrete | {a1:.2f} | 1.00 | **{D1:.1f}** | **{D1*2.54:.1f}** |
            | Base Course | {a2:.2f} | {m2:.2f} | **{D2:.1f}** | **{D2*2.54:.1f}** |
            | Subbase | {a3:.2f} | {m3:.2f} | **{D3:.1f}** | **{D3*2.54:.1f}** |
            """)
            
            # คำนวณ SN แต่ละชั้น
            SN1 = a1 * D1
            SN2 = a2 * D2 * m2
            SN3 = a3 * D3 * m3
            SN_total = SN1 + SN2 + SN3
            
            st.subheader("📊 Structural Number Contribution")
            st.markdown(f"""
            | Layer | SN Value | Percentage |
            |-------|----------|------------|
            | Asphalt (SN₁) | {SN1:.2f} | {(SN1/SN_total*100):.1f}% |
            | Base (SN₂) | {SN2:.2f} | {(SN2/SN_total*100):.1f}% |
            | Subbase (SN₃) | {SN3:.2f} | {(SN3/SN_total*100):.1f}% |
            | **Total** | **{SN_total:.2f}** | **100%** |
            """)
            
            # Simple visualization
            st.subheader("📐 Layer Thickness Visualization")
            st.progress(D1/20, text=f"Asphalt: {D1:.1f}\" ({D1*2.54:.1f} cm)")
            st.progress(D2/20, text=f"Base: {D2:.1f}\" ({D2*2.54:.1f} cm)")
            st.progress(D3/25, text=f"Subbase: {D3:.1f}\" ({D3*2.54:.1f} cm)")
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    
    with col2:
        st.header("ℹ️ Design Summary")
        
        st.markdown(f"""
        | Parameter | Value |
        |-----------|-------|
        | W18 (ESAL) | {W18:,.0f} |
        | Reliability | {reliability}% |
        | ZR | {ZR:.3f} |
        | So | {So:.2f} |
        | ΔPSI | {delta_psi:.1f} |
        | MR (psi) | {MR:,.0f} |
        | **Required SN** | **{SN_required:.2f}** |
        """)
        
        st.markdown("---")
        st.subheader("📋 Design Notes")
        st.info("""
        **AASHTO 1993 Method**
        
        - ผิวทางยืดหยุ่น (Flexible Pavement)
        - SN = Structural Number
        - W18 = 18-kip ESAL
        - MR = Resilient Modulus
        
        **Typical Values:**
        - Reliability: 80-95%
        - ΔPSI: 1.5-2.0
        - MR: 3,000-15,000 psi
        """)
        
        st.markdown("---")
        st.subheader("💾 Export Results")
        
        if st.button("📄 Generate Report"):
            report = f"""
AASHTO 1993 PAVEMENT DESIGN REPORT
{'='*50}

INPUT PARAMETERS:
- W18: {W18:,.0f}
- Reliability: {reliability}% (ZR = {ZR:.3f})
- Standard Error: {So:.2f}
- ΔPSI: {delta_psi:.1f}
- MR: {MR:,.0f} psi

LAYER COEFFICIENTS:
- a1 (Asphalt): {a1:.2f}
- a2 (Base): {a2:.2f}
- a3 (Subbase): {a3:.2f}

DRAINAGE COEFFICIENTS:
- m2: {m2:.2f}
- m3: {m3:.2f}

RESULTS:
- Required SN: {SN_required:.2f}

LAYER THICKNESSES:
- Asphalt: {D1:.1f} in ({D1*2.54:.1f} cm)
- Base: {D2:.1f} in ({D2*2.54:.1f} cm)
- Subbase: {D3:.1f} in ({D3*2.54:.1f} cm)

STRUCTURAL NUMBERS:
- SN1: {SN1:.2f}
- SN2: {SN2:.2f}
- SN3: {SN3:.2f}
- Total: {SN_total:.2f}
{'='*50}
            """
            st.download_button(
                "💾 Download Report",
                report,
                "pavement_design_report.txt",
                "text/plain"
            )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>AASHTO 1993 Flexible Pavement Design Calculator</p>
        <p>สำหรับการศึกษา - ควรตรวจสอบโดยวิศวกร</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
