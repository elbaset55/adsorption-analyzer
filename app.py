import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import plotly.graph_objects as go

# --- 1. تعريف الموديلات الرياضية ---
def langmuir_model(Ce, qmax, KL):
    return (qmax * KL * Ce) / (1 + KL * Ce)

def freundlich_model(Ce, KF, n):
    return KF * (Ce ** (1 / n))

def pfo_model(t, qe, k1):
    return qe * (1 - np.exp(-k1 * t))

def pso_model(t, qe, k2):
    return (k2 * (qe**2) * t) / (1 + k2 * qe * t)

def intraparticle_model(t_half, kid, C):
    return kid * t_half + C

# --- 2. إعدادات واجهة المستخدم ---
st.set_page_config(page_title="Comprehensive Adsorption Analyzer", layout="wide")
st.title("🔬 Comprehensive Adsorption & Kinetics Analyzer Pro")
st.write("أداة متكاملة لحسابات الاتزان، الحركية، الثرموديناميكا، ومنحنيات المعايرة الضوئية")

# تقسيم التطبيق إلى أقسام رئيسية (Tabs)
tab1, tab2, tab3, tab4 = st.tabs([
    "📉 1. منحنى المعايرة والامتصاصية", 
    "📊 2. دراسات الاتزان (Isotherms)", 
    "⏱️ 3. الحسابات الحركية (Kinetics)", 
    "🌡️ 4. الثرموديناميكا (Thermodynamics)"
])

# --- TAB 1: CALIBRATION & ABSORBANCE ---
with tab1:
    st.header("📉 حسابات الامتصاصية ومنحنى المعايرة")
    
    cal_method = st.radio("اختر طريقة حساب التركيز ($C$):", 
                          ["استخدام الامتصاصية المولية (Molar Absorptivity - Beer-Lambert)", 
                           "استخدام منحنى معايرة قياسي (Standard Calibration Curve: Y = mX + C)"])
    
    if cal_method == "استخدام الامتصاصية المولية (Molar Absorptivity - Beer-Lambert)":
        col1, col2 = st.columns(2)
        with col1:
            epsilon = st.number_input("الامتصاصية المولية ε (L/mol·cm):", value=15000.0)
            path_length = st.number_input("طول مسار الضوء b (cm):", value=1.0)
            mw = st.number_input("الوزن الجزيئي للملوث (g/mol) [للتحويل إلى mg/L]:", value=319.85)
        with col2:
            st.info("💡 قانون بير-لامبرت: $A = ε \cdot b \cdot C$\n\nحيث يتم تحويل التركيز تلقائياً من الملارية إلى mg/L باستخدام الوزن الجزيئي.")
            
    else:
        col1, col2 = st.columns(2)
        with col1:
            slope = st.number_input("ميل الخط المستقيم (Slope - m):", value=0.1)
            intercept = st.number_input("الجزء المقطوع (Intercept - C):", value=0.0)
        with col2:
            st.info("💡 المعادلة: $Absorbance = (Slope \cdot Concentration) + Intercept$\n\nيتم حساب التركيز: $C = (Abs - Intercept) / Slope$")

# --- TAB 2: EQUILIBRIUM STUDIES ---
with tab2:
    st.header("📊 دراسات الاتزان ونماذج الأيزوثيرم")
    st.write("ارفع ملف يحتوي على البيانات التجريبية لحساب سعة الأدمصاص وتوفيق الموديلات.")
    
    col1, col2 = st.columns(2)
    with col1:
        v_l = st.number_input("حجم المحلول V (L):", value=0.05, format="%.3f")
    with col2:
        m_g = st.number_input("كتلة المادة المادّة m (g):", value=0.1, format="%.3f")
        
    uploaded_iso = st.file_uploader("ارفع ملف الاتزان (Excel/CSV) يحتوي على [C0] و [Absorbance]", type=["xlsx", "csv"], key="iso")
    
    if uploaded_iso is not None:
        df_iso = pd.read_excel(uploaded_iso) if uploaded_iso.name.endswith('.xlsx') else pd.read_csv(uploaded_iso)
        
        if 'C0' in df_iso.columns and 'Absorbance' in df_iso.columns:
            # حساب التركيز عند الاتزان Ce
            if "الامتصاصية المولية" in cal_method:
                df_iso['Ce'] = (df_iso['Absorbance'] / (epsilon * path_length)) * mw * 1000 # تحويل لـ mg/L
            else:
                df_iso['Ce'] = (df_iso['Absorbance'] - intercept) / slope
                
            # حساب qe
            df_iso['qe'] = ((df_iso['C0'] - df_iso['Ce']) * v_l) / m_g
            df_iso['Removal_Efficiency_%'] = ((df_iso['C0'] - df_iso['Ce']) / df_iso['C0']) * 100
            
            st.write("### 📋 البيانات المحسوبة للاتزان:")
            st.dataframe(df_iso[['C0', 'Absorbance', 'Ce', 'qe', 'Removal_Efficiency_%']])
            
            Ce_data = df_iso['Ce'].values
            qe_data = df_iso['qe'].values
            
            try:
                # Fitting Langmuir
                popt_l, _ = curve_fit(langmuir_model, Ce_data, qe_data, p0=[max(qe_data), 1.0], bounds=(0, np.inf))
                qmax_fit, KL_fit = popt_l
                r2_l = 1 - (np.sum((qe_data - langmuir_model(Ce_data, *popt_l)) ** 2) / np.sum((qe_data - np.mean(qe_data)) ** 2))
                
                # Fitting Freundlich
                popt_f, _ = curve_fit(freundlich_model, Ce_data, qe_data, p0=[1.0, 1.0], bounds=(0, np.inf))
                KF_fit, n_fit = popt_f
                r2_f = 1 - (np.sum((qe_data - freundlich_model(Ce_data, *popt_f)) ** 2) / np.sum((qe_data - np.mean(qe_data)) ** 2))
                
                st.success(f"🎯 الموديل الأفضل لبياناتك هو: **{'Langmuir (سطح متجانس طبقة واحدة)' if r2_l > r2_f else 'Freundlich (سطح غير متجانس طبقات متعددة)'}**")
                
                # رسم المنحنى
                fig_iso = go.Figure()
                fig_iso.add_trace(go.Scatter(x=Ce_data, y=qe_data, mode='markers', name='البيانات التجريبية', marker=dict(color='red', size=10)))
                Ce_line = np.linspace(min(Ce_data)*0.8, max(Ce_data)*1.2, 100)
                fig_iso.add_trace(go.Scatter(x=Ce_line, y=langmuir_model(Ce_line, qmax_fit, KL_fit), mode='lines', name=f'Langmuir (R²={r2_l:.4f})'))
                fig_iso.add_trace(go.Scatter(x=Ce_line, y=freundlich_model(Ce_line, KF_fit, n_fit), mode='lines', name=f'Freundlich (R²={r2_f:.4f})', line=dict(dash='dash')))
                fig_iso.update_layout(xaxis_title="Ce (mg/L)", yaxis_title="qe (mg/g)", template="plotly_white")
                st.plotly_chart(fig_iso)
                
            except Exception as e:
                st.error(f"خطأ في معالجة الموديلات: {e}")

# --- TAB 3: KINETIC STUDIES ---
with tab3:
    st.header("⏱️ دراسات الحركية ومعدل الأدمصاص")
    st.write("ارفع ملف يحتوي على [Time] بالدقائق والـ [Absorbance] عند كل وقت.")
    
    c0_kin = st.number_input("التركيز الابتدائي للتجربة الحركية C0 (mg/L):", value=50.0)
    uploaded_kin = st.file_uploader("ارفع ملف الحركية (Excel/CSV) يحتوي على [Time] و [Absorbance]", type=["xlsx", "csv"], key="kin")
    
    if uploaded_kin is not None:
        df_kin = pd.read_excel(uploaded_kin) if uploaded_kin.name.endswith('.xlsx') else pd.read_csv(uploaded_kin)
        
        if 'Time' in df_kin.columns and 'Absorbance' in df_kin.columns:
            if "الامتصاصية المولية" in cal_method:
                df_kin['Ct'] = (df_kin['Absorbance'] / (epsilon * path_length)) * mw * 1000
            else:
                df_kin['Ct'] = (df_kin['Absorbance'] - intercept) / slope
                
            df_kin['qt'] = ((c0_kin - df_kin['Ct']) * v_l) / m_g
            
            st.write("### 📋 البيانات الحركية المحسوبة:")
            st.dataframe(df_kin[['Time', 'Absorbance', 'Ct', 'qt']])
            
            t_data = df_kin['Time'].values
            qt_data = df_kin['qt'].values
            
            try:
                # Fitting PFO
                popt_pfo, _ = curve_fit(pfo_model, t_data, qt_data, p0=[max(qt_data), 0.01], bounds=(0, np.inf))
                r2_pfo = 1 - (np.sum((qt_data - pfo_model(t_data, *popt_pfo)) ** 2) / np.sum((qt_data - np.mean(qt_data)) ** 2))
                
                # Fitting PSO
                popt_pso, _ = curve_fit(pso_model, t_data, qt_data, p0=[max(qt_data), 0.01], bounds=(0, np.inf))
                r2_pso = 1 - (np.sum((qt_data - pso_model(t_data, *popt_pso)) ** 2) / np.sum((qt_data - np.mean(qt_data)) ** 2))
                
                st.write(f"**Pseudo-first-order (R²):** {r2_pfo:.4f} | **k₁:** {popt_pfo[1]:.4f} min⁻¹")
                st.write(f"**Pseudo-second-order (R²):** {r2_pso:.4f} | **k₂:** {popt_pso[1]:.4f} g/mg·min")
                
                # رسم حركي
                fig_kin = go.Figure()
                fig_kin.add_trace(go.Scatter(x=t_data, y=qt_data, mode='markers', name='Experimental qt'))
                t_line = np.linspace(0, max(t_data), 100)
                fig_kin.add_trace(go.Scatter(x=t_line, y=pfo_model(t_line, *popt_pfo), mode='lines', name='PFO Fit'))
                fig_kin.add_trace(go.Scatter(x=t_line, y=pso_model(t_line, *popt_pso), mode='lines', name='PSO Fit', line=dict(dash='dash')))
                fig_kin.update_layout(xaxis_title="Time (min)", yaxis_title="qt (mg/g)", template="plotly_white")
                st.plotly_chart(fig_kin)
            except Exception as e:
                st.error(f"خطأ في حسابات الحركية: {e}")

# --- TAB 4: THERMODYNAMICS ---
with tab4:
    st.header("🌡️ الحسابات الثرموديناميكية (Thermodynamics)")
    st.write("أدخل قيم ثابت التوزيع ($K_c$ أو $K_d$) عند درجات حرارة مختلفة لحساب ΔG° و ΔH° و ΔS° تلقائياً عبر معادلة فانت هوف (Van 't Hoff).")
    
    st.info("💡 المعادلة المستخدمة: $\ln(K_c) = \frac{\Delta S^\circ}{R} - \frac{\Delta H^\circ}{R \cdot T}$")
    
    # جدول يدوي لإدخال البيانات الحركية
    num_temps = st.number_input("عدد درجات الحرارة المقاسة (مثلاً 3 أو 4):", min_value=2, max_value=10, value=3)
    
    thermo_data = []
    cols = st.columns(num_temps)
    for i, col in enumerate(cols):
        with col:
            t_c = st.number_input(f"الحرارة {i+1} (°C):", value=25.0 + i*15)
            kc = st.number_input(f"ثابت الاتزان $K_c$ عند {t_c}°C:", value=2.0 + i*1.5, format="%.4f")
            thermo_data.append({"T_C": t_c, "Kc": kc})
            
    df_th = pd.DataFrame(thermo_data)
    df_th['T_K'] = df_th['T_C'] + 273.15
    df_th['1/T'] = 1 / df_th['T_K']
    df_th['ln_Kc'] = np.log(df_th['Kc'])
    
    R = 8.314 # J/mol·K
    
    try:
        # حساب الانحدار الخطي لمعادلة فانت هوف Y = mX + C
        # Y = ln_Kc, X = 1/T
        slope_th, intercept_th = np.polyfit(df_th['1/T'], df_th['ln_Kc'], 1)
        
        delta_H = -slope_th * R / 1000 # kJ/mol
        delta_S = intercept_th * R # J/mol·K
        
        df_th['Delta_G_kJ_mol'] = (-R * df_th['T_K'] * df_th['ln_Kc']) / 1000
        
        st.subheader("🏆 النتائج الثرموديناميكية:")
        st.write(f"**المحتوى الحراري ($\Delta H^\circ$):** {delta_H:.3f} kJ/mol")
        st.write(f"**الإنتروبي ($\Delta S^\circ$):** {delta_S:.3f} J/mol·K")
        
        if delta_H < 0:
            st.warning("🔥 التفاعل **طارد للحرارة (Exothermic)**: الأدمصاص يقل بزيادة الحرارة (غالباً Physisorption).")
        else:
            st.success("❄️ التفاعل **ماص للحرارة (Endothermic)**: الأدمصاص يزيد بزيادة الحرارة (غالباً Chemisorption).")
            
        st.write("### قيم طاقة جيبس الحرة ($\Delta G^\circ$) عند كل درجة:")
        st.dataframe(df_th[['T_C', 'Kc', 'Delta_G_kJ_mol']])
        
    except Exception as e:
        st.error(f"يرجى التحقق من المدخلات الثرموديناميكية: {e}")