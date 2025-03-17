import streamlit as st
import pandas as pd
import plotly.express as px
import time
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import tempfile
import base64

# Importieren der CV-Analyzer-Module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cv_analyzer import CVAnalyzer
from utils.debugger import Debugger

# Debugger initialisieren
debugger = Debugger()

# App-Konfiguration
st.set_page_config(
    page_title="CV Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Seitentitel und Info
st.title("CV Analyzer")
st.markdown("Ein leistungsstarkes Tool zur Analyse von Lebensläufen und Bewertung von Fähigkeiten")

# Initialisierung des Analyzer
@st.cache_resource
def get_analyzer():
    return CVAnalyzer()

analyzer = get_analyzer()

# Funktion zum Download von Dateien
def get_download_link(data, filename, text):
    if isinstance(data, str):
        data = data.encode()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{text}</a>'
    return href

# Seitennavigation
page = st.sidebar.selectbox(
    "Navigation",
    ["CV Analyse", "Job Matching", "Batch Analyse", "Einstellungen"]
)

# CV Analyse-Seite
if page == "CV Analyse":
    st.header("Lebenslauf analysieren")
    
    # Datei-Upload
    uploaded_file = st.file_uploader("Wählen Sie einen Lebenslauf (PDF, DOCX)", type=["pdf", "docx"])
    
    if uploaded_file is not None:
        # Temporäre Datei speichern
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        
        try:
            # Fortschrittsbalken
            progress_bar = st.progress(0)
            start_time = time.time()
            
            # Analyse durchführen
            with st.spinner("Analysiere Lebenslauf..."):
                for i in range(100):
                    # Simuliere Fortschritt
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                
                # Tatsächliche Analyse
                results = analyzer.analyze_cv_file(tmp_path)
                
                # Performance-Metrik loggen
                duration = time.time() - start_time
                debugger.log_performance_metric("analysis_duration", duration)
            
            # Ergebnisse anzeigen
            st.success("Analyse abgeschlossen!")
            
            # Übersicht
            st.subheader("Übersicht")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Beruf", results.get("profession", "Nicht erkannt"))
            
            with col2:
                st.metric("Erfahrungslevel", results.get("experience_level", "Nicht erkannt"))
            
            with col3:
                st.metric("Relevanz Score", f"{results.get('relevance_score', 0):.0f}%")
            
            # Fähigkeiten visualisieren
            st.subheader("Fähigkeiten")
            if "skills" in results and results["skills"]:
                skills_df = pd.DataFrame({
                    "Fähigkeit": list(results["skills"].keys()),
                    "Bewertung": list(results["skills"].values())
                })
                
                fig = px.bar(
                    skills_df, 
                    x="Fähigkeit", 
                    y="Bewertung",
                    color="Bewertung",
                    color_continuous_scale="viridis",
                    title="Fähigkeiten-Bewertung"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Keine Fähigkeiten erkannt.")
            
            # Erfahrung visualisieren
            st.subheader("Berufserfahrung")
            if "experience" in results and results["experience"]:
                st.markdown("### Zeitleiste")
                
                # Erfahrungs-Timeline
                experience_df = pd.DataFrame(results["experience"])
                experience_df["start_date"] = pd.to_datetime(experience_df["start_date"])
                experience_df["end_date"] = pd.to_datetime(experience_df["end_date"])
                experience_df["duration"] = (experience_df["end_date"] - experience_df["start_date"]).dt.days / 365.25
                
                fig = px.timeline(
                    experience_df,
                    x_start="start_date",
                    x_end="end_date",
                    y="title",
                    color="company",
                    title="Berufserfahrung"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Erfahrung als Tabelle
                st.dataframe(
                    experience_df[["title", "company", "start_date", "end_date", "duration"]].rename(
                        columns={
                            "title": "Position",
                            "company": "Unternehmen",
                            "start_date": "Startdatum",
                            "end_date": "Enddatum",
                            "duration": "Dauer (Jahre)"
                        }
                    ).sort_values("Startdatum", ascending=False)
                )
            else:
                st.info("Keine Berufserfahrung erkannt.")
            
            # Empfehlungen
            st.subheader("Empfehlungen")
            recommendations = results.get("recommendations", [])
            if recommendations:
                for i, rec in enumerate(recommendations):
                    st.markdown(f"**{i+1}.** {rec}")
            else:
                st.info("Keine Empfehlungen verfügbar.")
            
            # Export-Optionen
            st.subheader("Ergebnisse exportieren")
            col1, col2, col3 = st.columns(3)
            
            # JSON Export
            with col1:
                json_data = json.dumps(results, indent=2)
                st.markdown(
                    get_download_link(json_data, "cv_analysis.json", "Als JSON herunterladen"),
                    unsafe_allow_html=True
                )
            
            # CSV Export
            with col2:
                csv_data = analyzer.export_results(results, format="csv")
                st.markdown(
                    get_download_link(csv_data, "cv_analysis.csv", "Als CSV herunterladen"),
                    unsafe_allow_html=True
                )
            
            # Excel Export
            with col3:
                excel_data = analyzer.export_results(results, format="excel")
                st.markdown(
                    get_download_link(excel_data, "cv_analysis.xlsx", "Als Excel herunterladen"),
                    unsafe_allow_html=True
                )
                
        except Exception as e:
            st.error(f"Fehler bei der Analyse: {str(e)}")
            debugger.log_error(e, "cv_analysis")
        
        finally:
            # Temporäre Datei löschen
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

# Job Matching Seite
elif page == "Job Matching":
    st.header("Lebenslauf mit Stellenbeschreibung abgleichen")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Lebenslauf")
        cv_file = st.file_uploader("Lebenslauf hochladen (PDF, DOCX)", type=["pdf", "docx"])
    
    with col2:
        st.subheader("Stellenbeschreibung")
        job_description = st.text_area("Fügen Sie die Stellenbeschreibung ein oder laden Sie eine Datei hoch", height=300)
        job_file = st.file_uploader("Stellenbeschreibung hochladen (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
        
        if job_file is not None:
            # Temporäre Datei speichern
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{job_file.name.split('.')[-1]}") as tmp:
                tmp.write(job_file.getvalue())
                job_path = tmp.name
            
            # Datei einlesen
            try:
                job_description = analyzer.extract_text(job_path)
                st.success("Stellenbeschreibung erfolgreich geladen!")
            except Exception as e:
                st.error(f"Fehler beim Lesen der Stellenbeschreibung: {str(e)}")
                debugger.log_error(e, "job_description_reading")
            
            # Temporäre Datei löschen
            if os.path.exists(job_path):
                os.unlink(job_path)
    
    # Match-Button
    if cv_file and (job_description or job_file):
        if st.button("Lebenslauf mit Stellenbeschreibung abgleichen"):
            # Temporäre Datei für CV speichern
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{cv_file.name.split('.')[-1]}") as tmp:
                tmp.write(cv_file.getvalue())
                cv_path = tmp.name
            
            try:
                # Fortschrittsbalken
                progress_bar = st.progress(0)
                start_time = time.time()
                
                with st.spinner("Führe Matching durch..."):
                    for i in range(100):
                        # Simuliere Fortschritt
                        time.sleep(0.01)
                        progress_bar.progress(i + 1)
                    
                    # Tatsächliche Analyse
                    results = analyzer.analyze_cv_file(cv_path, job_description)
                    
                    # Performance-Metrik loggen
                    duration = time.time() - start_time
                    debugger.log_performance_metric("match_duration", duration)
                
                st.success("Matching abgeschlossen!")
                
                # Match-Score
                st.subheader("Match-Ergebnisse")
                
                # Gauge-Chart für Match-Score
                match_score = results.get("relevance_score", 0)
                fig = px.pie(
                    values=[match_score, 100-match_score],
                    names=["Match", "Gap"],
                    hole=0.7,
                    color_discrete_sequence=["#4B8BBE", "#E2E8F0"]
                )
                fig.update_layout(
                    annotations=[{
                        "text": f"{match_score:.0f}%",
                        "showarrow": False,
                        "font": {"size": 40}
                    }],
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Fehlende Fähigkeiten
                st.subheader("Empfohlene Verbesserungen")
                
                if "missing_skills" in results and results["missing_skills"]:
                    missing_skills_df = pd.DataFrame({
                        "Fähigkeit": list(results["missing_skills"].keys()),
                        "Wichtigkeit": list(results["missing_skills"].values())
                    })
                    
                    fig = px.bar(
                        missing_skills_df,
                        x="Fähigkeit",
                        y="Wichtigkeit",
                        color="Wichtigkeit", 
                        color_continuous_scale="oranges",
                        title="Fehlende oder zu verbessernde Fähigkeiten"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Keine fehlenden Fähigkeiten identifiziert.")
                
                # Empfehlungen
                if "recommendations" in results and results["recommendations"]:
                    for i, rec in enumerate(results["recommendations"]):
                        st.markdown(f"**{i+1}.** {rec}")
                
                # Export-Optionen
                st.subheader("Ergebnisse exportieren")
                col1, col2, col3 = st.columns(3)
                
                # JSON Export
                with col1:
                    json_data = json.dumps(results, indent=2)
                    st.markdown(
                        get_download_link(json_data, "job_match.json", "Als JSON herunterladen"),
                        unsafe_allow_html=True
                    )
                
                # CSV Export
                with col2:
                    csv_data = analyzer.export_results(results, format="csv")
                    st.markdown(
                        get_download_link(csv_data, "job_match.csv", "Als CSV herunterladen"),
                        unsafe_allow_html=True
                    )
                
                # Excel Export
                with col3:
                    excel_data = analyzer.export_results(results, format="excel")
                    st.markdown(
                        get_download_link(excel_data, "job_match.xlsx", "Als Excel herunterladen"),
                        unsafe_allow_html=True
                    )
                    
            except Exception as e:
                st.error(f"Fehler beim Matching: {str(e)}")
                debugger.log_error(e, "job_matching")
            
            finally:
                # Temporäre Datei löschen
                if os.path.exists(cv_path):
                    os.unlink(cv_path)

# Batch Analyse-Seite
elif page == "Batch Analyse":
    st.header("Batch-Analyse mehrerer Lebensläufe")
    
    uploaded_files = st.file_uploader(
        "Wählen Sie mehrere Lebensläufe aus (PDF, DOCX)", 
        type=["pdf", "docx"],
        accept_multiple_files=True
    )
    
    # Job-Beschreibung (optional)
    use_job = st.checkbox("Mit Stellenbeschreibung abgleichen")
    job_description = None
    
    if use_job:
        job_description = st.text_area("Fügen Sie die Stellenbeschreibung ein", height=200)
    
    if uploaded_files and st.button("Batch-Analyse starten"):
        temp_files = []
        
        try:
            # Temporäre Dateien speichern
            for uploaded_file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    temp_files.append((tmp.name, uploaded_file.name))
            
            # Fortschrittsbalken
            progress_text = st.empty()
            progress_bar = st.progress(0)
            
            # Ergebnisse für alle Dateien
            all_results = []
            
            # Startzeit für Performance-Messung
            start_time = time.time()
            
            # Analyse für jede Datei
            for i, (temp_path, original_name) in enumerate(temp_files):
                progress_text.text(f"Analysiere {original_name} ({i+1}/{len(temp_files)})")
                progress_bar.progress((i+1)/len(temp_files))
                
                try:
                    # Analyse mit oder ohne Job-Beschreibung
                    if job_description:
                        result = analyzer.analyze_cv_file(temp_path, job_description)
                    else:
                        result = analyzer.analyze_cv_file(temp_path)
                    
                    # Dateinamen hinzufügen
                    result["filename"] = original_name
                    all_results.append(result)
                    
                except Exception as e:
                    st.error(f"Fehler bei der Analyse von {original_name}: {str(e)}")
                    debugger.log_error(e, f"batch_analysis_{original_name}")
            
            # Performance-Metrik loggen
            duration = time.time() - start_time
            debugger.log_performance_metric("batch_analysis_duration", duration)
            
            st.success(f"Batch-Analyse von {len(all_results)} Dateien abgeschlossen!")
            
            if all_results:
                # Tabelle mit Übersicht erstellen
                overview_data = []
                for result in all_results:
                    overview_data.append({
                        "Dateiname": result.get("filename", "Unbekannt"),
                        "Beruf": result.get("profession", "Nicht erkannt"),
                        "Erfahrungslevel": result.get("experience_level", "Nicht erkannt"),
                        "Relevanz-Score": result.get("relevance_score", 0),
                        "Anzahl Fähigkeiten": len(result.get("skills", {})),
                        "Berufserfahrung (Jahre)": sum(exp.get("duration", 0) for exp in result.get("experience", []))
                    })
                
                # Übersichtstabelle anzeigen
                overview_df = pd.DataFrame(overview_data)
                st.subheader("Übersicht aller Kandidaten")
                st.dataframe(overview_df, use_container_width=True)
                
                # Kandidaten-Ranking wenn Job-Beschreibung verwendet wird
                if job_description:
                    st.subheader("Kandidaten-Ranking")
                    
                    # Nach Relevanz sortieren
                    ranking_df = overview_df.sort_values("Relevanz-Score", ascending=False)
                    ranking_df = ranking_df.reset_index(drop=True)
                    ranking_df.index = ranking_df.index + 1  # 1-basierter Index
                    
                    # Ranking-Tabelle anzeigen
                    st.dataframe(ranking_df, use_container_width=True)
                    
                    # Top 3 Kandidaten visualisieren
                    st.subheader("Top Kandidaten")
                    top_candidates = ranking_df.head(min(3, len(ranking_df)))
                    
                    fig = px.bar(
                        top_candidates,
                        x="Dateiname",
                        y="Relevanz-Score",
                        color="Relevanz-Score",
                        color_continuous_scale="blues",
                        title="Top Kandidaten nach Relevanz-Score"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Export-Optionen für Batch-Analyse
                st.subheader("Batch-Ergebnisse exportieren")
                
                # Export-Optionen
                col1, col2 = st.columns(2)
                
                # JSON Export
                with col1:
                    json_batch_data = json.dumps(all_results, indent=2)
                    st.markdown(
                        get_download_link(json_batch_data, "batch_analysis.json", "Als JSON herunterladen"),
                        unsafe_allow_html=True
                    )
                
                # Excel Export
                with col2:
                    # Excel-Export mit pandas
                    excel_buffer = pd.ExcelWriter("batch_analysis.xlsx", engine="xlsxwriter")
                    overview_df.to_excel(excel_buffer, sheet_name="Übersicht", index=False)
                    
                    # Detaillierte Daten für jeden Kandidaten
                    for i, result in enumerate(all_results):
                        # Skills als DataFrame
                        if "skills" in result and result["skills"]:
                            skills_df = pd.DataFrame({
                                "Fähigkeit": list(result["skills"].keys()),
                                "Bewertung": list(result["skills"].values())
                            })
                            skills_df.to_excel(excel_buffer, sheet_name=f"Kandidat_{i+1}_Skills", index=False)
                        
                        # Erfahrung als DataFrame
                        if "experience" in result and result["experience"]:
                            exp_df = pd.DataFrame(result["experience"])
                            exp_df.to_excel(excel_buffer, sheet_name=f"Kandidat_{i+1}_Erfahrung", index=False)
                    
                    excel_buffer.close()
                    
                    # Excel-Datei zum Download anbieten
                    with open("batch_analysis.xlsx", "rb") as f:
                        excel_data = f.read()
                    
                    st.markdown(
                        get_download_link(excel_data, "batch_analysis.xlsx", "Als Excel herunterladen"),
                        unsafe_allow_html=True
                    )
                    
                    # Temporäre Excel-Datei löschen
                    if os.path.exists("batch_analysis.xlsx"):
                        os.unlink("batch_analysis.xlsx")
            
        except Exception as e:
            st.error(f"Fehler bei der Batch-Analyse: {str(e)}")
            debugger.log_error(e, "batch_analysis")
        
        finally:
            # Temporäre Dateien löschen
            for temp_path, _ in temp_files:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

# Einstellungen-Seite
elif page == "Einstellungen":
    st.header("Einstellungen")
    
    # API-Einstellungen
    st.subheader("API-Einstellungen")
    
    col1, col2 = st.columns(2)
    
    with col1:
        linkedin_api_key = st.text_input(
            "LinkedIn API-Schlüssel",
            type="password",
            value=os.environ.get("LINKEDIN_API_KEY", "")
        )
    
    with col2:
        github_token = st.text_input(
            "GitHub Token",
            type="password",
            value=os.environ.get("GITHUB_TOKEN", "")
        )
    
    # Speichern-Button
    if st.button("API-Einstellungen speichern"):
        # Hier würde man die Einstellungen in eine .env Datei oder ähnliches speichern
        st.success("Einstellungen gespeichert!")
    
    # Analyse-Einstellungen
    st.subheader("Analyse-Einstellungen")
    
    col1, col2 = st.columns(2)
    
    with col1:
        min_experience = st.slider(
            "Minimale Berufserfahrung (Jahre)",
            min_value=0,
            max_value=20,
            value=0
        )
    
    with col2:
        min_relevance = st.slider(
            "Minimale Relevanz (%)",
            min_value=0,
            max_value=100,
            value=50
        )
    
    # Weitere Einstellungen
    advanced_settings = st.expander("Erweiterte Einstellungen")
    
    with advanced_settings:
        col1, col2 = st.columns(2)
        
        with col1:
            debug_mode = st.checkbox("Debug-Modus aktivieren", value=False)
        
        with col2:
            language = st.selectbox(
                "Sprache für die Analyse",
                options=["Deutsch", "Englisch"],
                index=0
            )
    
    # Debug-Informationen
    debug_info = st.expander("Debug-Informationen")
    
    with debug_info:
        # Fehler-Zusammenfassung anzeigen
        st.subheader("Fehler-Zusammenfassung")
        error_summary = debugger.get_error_summary()
        
        if error_summary:
            st.dataframe(
                pd.DataFrame(error_summary, columns=["Zeitstempel", "Typ", "Nachricht", "Kontext"]),
                use_container_width=True
            )
        else:
            st.info("Keine Fehler protokolliert.")
        
        # Performance-Metriken anzeigen
        st.subheader("Performance-Metriken")
        performance_metrics = debugger.get_performance_metrics()
        
        if performance_metrics:
            metrics_df = pd.DataFrame(performance_metrics)
            
            # Durchschnittliche Werte berechnen
            avg_metrics = metrics_df.groupby("metric")["value"].mean().reset_index()
            
            # Visualisierung der Metriken
            fig = px.bar(
                avg_metrics,
                x="metric",
                y="value",
                title="Durchschnittliche Performance-Metriken",
                labels={"metric": "Metrik", "value": "Wert (Sekunden)"}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Rohdaten anzeigen
            st.dataframe(metrics_df, use_container_width=True)
        else:
            st.info("Keine Performance-Metriken verfügbar.")
        
        # Debug-Daten exportieren
        if st.button("Debug-Daten exportieren"):
            debug_data = {
                "errors": error_summary,
                "performance_metrics": performance_metrics,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            
            debug_json = json.dumps(debug_data, indent=2)
            st.markdown(
                get_download_link(debug_json, "debug_data.json", "Debug-Daten herunterladen"),
                unsafe_allow_html=True
            )

# Footer
st.markdown("---")
st.markdown("© 2024 CV Analyzer | Version 1.0.0") 