import io
import pandas as pd
import requests
import streamlit as st

# In docker-compose this resolves to the backend service; for local testing use http://localhost:7860
BACKEND_URL = "http://backend:7860"

st.set_page_config(page_title="SuperKart Sales Predictor", layout="centered")
st.title("SuperKart - Product Sales Prediction")
st.caption("Predict total product sales per store, one product or a whole batch at a time.")

tab_single, tab_batch = st.tabs(["Single prediction", "Batch prediction"])

with tab_single:
    st.subheader("Enter product and store details")
    col1, col2 = st.columns(2)
    with col1:
        product_weight = st.number_input("Product Weight (kg)", min_value=0.0, value=12.0, step=0.1)
        product_sugar_content = st.selectbox("Sugar content", ["Low Sugar", "Regular", "No Sugar"])
        product_allocated_area = st.number_input("Allocated shelf area (fraction)", min_value=0.0, value=0.05, step=0.01)
        product_mrp = st.number_input("Product MRP", min_value=0.0, value=150.0, step=1.0)
        product_id_char = st.selectbox("Product family", ["FD", "DR", "NC"])
    with col2:
        store_size = st.selectbox("Store size", ["Small", "Medium", "High"])
        store_location_city_type = st.selectbox("City tier", ["Tier 1", "Tier 2", "Tier 3"])
        # Values exactly as seen in training - an unseen category can never be submitted
        store_type = st.selectbox("Store type",
                                  ["Supermarket Type1", "Supermarket Type2",
                                   "Departmental Store", "Food Mart"])
        store_age_years = st.number_input("Store age (years)", min_value=0, value=16, step=1)
        product_type_category = st.selectbox("Broad category", ["Food", "Drinks", "Non-Consumables"])

    if st.button("Predict sales", type="primary"):
        payload = {
            "Product_Weight": product_weight,
            "Product_Sugar_Content": product_sugar_content,
            "Product_Allocated_Area": product_allocated_area,
            "Product_MRP": product_mrp,
            "Store_Size": store_size,
            "Store_Location_City_Type": store_location_city_type,
            "Store_Type": store_type,
            "Product_Id_char": product_id_char,
            "Store_Age_Years": store_age_years,
            "Product_Type_Category": product_type_category,
        }
        try:
            resp = requests.post(f"{BACKEND_URL}/v1/predict", json=payload, timeout=30)
            if resp.status_code == 200:
                st.success(f"Predicted total sales: {resp.json()['Sales']:,.2f}")
            else:
                st.error(f"Backend error ({resp.status_code}): {resp.json().get('error', resp.text)}")
        except requests.RequestException as e:
            st.error(f"Could not reach the backend at {BACKEND_URL}: {e}")

with tab_batch:
    st.subheader("Upload a batch CSV")
    st.caption("Columns: Product_Weight, Product_Sugar_Content, Product_Allocated_Area, Product_MRP, "
               "Store_Size, Store_Location_City_Type, Store_Type, Product_Id_char, "
               "Store_Age_Years, Product_Type_Category")
    uploaded = st.file_uploader("Choose a CSV file", type=["csv"])
    if uploaded is not None:
        batch_df = pd.read_csv(uploaded)
        st.write("Preview:", batch_df.head())
        if st.button("Predict batch", type="primary"):
            try:
                files = {"file": (uploaded.name, io.BytesIO(uploaded.getvalue()), "text/csv")}
                resp = requests.post(f"{BACKEND_URL}/v1/predictbatch", files=files, timeout=120)
                if resp.status_code == 200:
                    preds = resp.json()
                    out = batch_df.copy()
                    out["Predicted_Sales"] = [preds[str(i)] for i in range(len(out))]
                    st.success(f"Predicted {len(out)} rows")
                    st.write(out.head())
                    st.download_button("Download predictions",
                                       out.to_csv(index=False).encode(),
                                       file_name="superkart_batch_predictions.csv")
                else:
                    st.error(f"Backend error ({resp.status_code}): {resp.json().get('error', resp.text)}")
            except requests.RequestException as e:
                st.error(f"Could not reach the backend at {BACKEND_URL}: {e}")
