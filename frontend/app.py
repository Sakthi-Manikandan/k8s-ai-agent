import streamlit as st
import httpx
import json

# Page config
st.set_page_config(
    page_title="K8s AI Agent",
    page_icon="🤖",
    layout="wide"
)

# API URL
API_URL = "http://localhost:8000/api/v1"


def call_investigate(namespace: str) -> dict:
    """Calls FastAPI investigate endpoint"""
    try:
        with httpx.Client(timeout=300.0) as client:
            response = client.post(
                f"{API_URL}/investigate",
                json={"namespace": namespace}
            )
            return response.json()
    except Exception as e:
        return {"error": str(e)}


def call_approve(pipeline_id: str, action_index: int) -> dict:
    """Calls FastAPI approve endpoint"""
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{API_URL}/approve",
                json={
                    "pipeline_id": pipeline_id,
                    "action_index": action_index
                }
            )
            return response.json()
    except Exception as e:
        return {"error": str(e)}
    
    
def call_history() -> dict:
    """Gets investigation history from API"""
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{API_URL}/history")
            return response.json()
    except Exception as e:
        return {"error": str(e)}


# ─────────────────────────────────────
# HEADER
# ─────────────────────────────────────
st.title("🤖 K8s AI Troubleshooting Agent")
st.markdown(
    "AI-powered Kubernetes diagnostics with "
    "Human in the Loop approval system"
)
st.divider()

# ─────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configuration")

    namespace = st.selectbox(
        "Select Namespace",
        ["--all-namespaces", "default", "kube-system"],
        index=0
    )

    st.divider()
    st.markdown("### 📊 How it works")
    st.markdown("""
    1. Click Investigate
    2. AI analyzes cluster
    3. Review suggested actions
    4. Approve or Reject
    5. Agent executes approved fixes!
    """)

    st.divider()
    st.markdown("### 🔗 API")
    st.markdown("[Swagger Docs](http://localhost:8000/docs)")

# ─────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────

# Initialize session state
if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None
if "pipeline_id" not in st.session_state:
    st.session_state.pipeline_id = None
if "investigating" not in st.session_state:
    st.session_state.investigating = False

# Investigate button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    investigate_btn = st.button(
        "🔍 Investigate Cluster",
        type="primary",
        use_container_width=True
    )

if investigate_btn:
    st.session_state.investigating = True

    with st.status(
        "🔍 Investigating Kubernetes cluster...",
        expanded=True
    ) as status:
        st.write("✅ Connecting to cluster...")
        st.write("✅ Inspecting pods...")
        st.write("✅ Collecting logs...")
        st.write("✅ Analyzing events...")
        st.write("✅ Inspecting deployments...")
        st.write("✅ Checking networking...")
        st.write("🧠 AI reasoning in progress...")
        st.write("⏳ This may take 1-2 minutes...")

        result = call_investigate(namespace)
        #print("result>>>>>",result)
        if result.get("error") is not None:
           status.update(
             label="❌ Investigation failed!",
             state="error"
        )
           st.error(f"Error: {result['error']}")
        else:
            st.session_state.pipeline_result = result
            st.session_state.pipeline_id = result.get(
                "pipeline_id"
            )
            status.update(
                label="✅ Investigation complete!",
                state="complete"
            )

# Show results
if st.session_state.pipeline_result:
    result = st.session_state.pipeline_result
    st.divider()

    # Summary metrics
    st.subheader("📊 Cluster Summary")
    summary = result.get("summary", {})
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Total Pods",
            summary.get("total_pods", 0)
        )
    with col2:
        st.metric(
            "Problematic Pods",
            summary.get("problematic_pods", 0),
            delta=None
        )
    with col3:
        st.metric(
            "Critical Events",
            summary.get("critical_events", 0)
        )
    with col4:
        st.metric(
            "Network Issues",
            summary.get("network_issues", 0)
        )

    st.divider()

    # AI Diagnosis
    st.subheader("🧠 AI Diagnosis")
    diagnosis = result.get("diagnosis", {})

    if diagnosis:
        # Root cause
        st.error(
            f"🔴 Root Cause: "
            f"{diagnosis.get('root_cause', 'Unknown')}"
        )

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📋 Explanation")
            st.info(diagnosis.get(
                "explanation",
                "No explanation available"
            ))

            st.markdown("### 💡 Suggested Fix")
            st.success(diagnosis.get(
                "suggested_fix",
                "No fix available"
            ))

        with col2:
            st.markdown("### ⌨️ kubectl Commands")
            commands = diagnosis.get("kubectl_commands", [])
            if commands:
                for cmd in commands:
                    st.code(cmd, language="bash")
            else:
                st.info("No commands suggested")

            st.markdown("### 🛡️ Prevention")
            st.warning(diagnosis.get(
                "prevention",
                "No prevention advice"
            ))

        # Confidence score
        confidence = diagnosis.get("confidence", 0)
        st.markdown("### 🎯 Confidence Score")
        st.progress(
            confidence / 100,
            text=f"AI Confidence: {confidence}%"
        )

    st.divider()

    # Suggested Actions (Human in the Loop!)
    st.subheader("⚡ Suggested Actions")
    actions = result.get("suggested_actions", [])

    if actions:
        st.warning(
            "⚠️ Review carefully before approving! "
            "These actions will modify your cluster!"
        )

        for i, action in enumerate(actions):
            with st.expander(
                f"Action {i+1}: {action['action_type']} "
                f"- Risk: {action['risk']}",
                expanded=True
            ):
                st.markdown(f"Reason: {action['reason']}")
                st.code(action['command'], language="bash")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(
                        f"✅ Approve",
                        key=f"approve_{i}",
                        type="primary"
                    ):
                        with st.spinner("Executing action..."):
                            approve_result = call_approve(
                                st.session_state.pipeline_id,
                                i
                            )
                            if approve_result.get(
                                "status"
                            ) == "success":
                                st.success(
                                    f"✅ {approve_result.get('message')}"
                                )
                            else:
                                st.error(
                                    f"❌ Failed: {approve_result}"
                                )
                with col2:
                    if st.button(
                        f"❌ Reject",
                        key=f"reject_{i}"
                    ):
                        st.info("Action rejected!")
    else:
        st.success(
            "✅ No remediation actions needed! "
            "Cluster appears healthy!"
        )

    st.divider()
    st.caption(
        f"Pipeline ID: {st.session_state.pipeline_id}"
    )
    
# ─────────────────────────────────────
# INVESTIGATION HISTORY
# ─────────────────────────────────────
st.divider()
st.subheader("📋 Investigation History")

history = call_history()

if "error" not in history:
    stats = history.get("stats", {})

    # Stats row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Total Investigations",
            stats.get("total", 0)
        )
    with col2:
        st.metric(
            "Unhealthy Detected",
            stats.get("unhealthy", 0)
        )
    with col3:
        avg_conf = stats.get("avg_confidence")
        st.metric(
            "Avg Confidence",
            f"{round(avg_conf)}%" if avg_conf else "N/A"
        )

    # History table
    investigations = history.get("investigations", [])
    if investigations:
        for inv in investigations:
            healthy = inv.get("cluster_healthy", False)
            status_icon = "✅" if healthy else "🔴"

            with st.expander(
                f"{status_icon} "
                f"{inv.get('created_at', 'Unknown time')} "
                f"| {inv.get('namespace', 'default')} "
                f"| Confidence: {inv.get('confidence', 0)}%"
            ):
                st.markdown(
                    f"**Root Cause:** "
                    f"{inv.get('root_cause', 'None')}"
                )
                st.markdown(
                    f"**Pods:** {inv.get('total_pods', 0)} total, "
                    f"{inv.get('problematic_pods', 0)} problematic"
                )
                st.markdown(
                    f"**Pipeline ID:** {inv.get('id', '')}"
                )
    else:
        st.info(
            "No investigations yet! "
            "Click Investigate to start! 🔍"
        )