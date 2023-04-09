import streamlit as st
import googlemaps
import pandas as pd
from google.cloud import language_v1
import time
import plotly.express as px

# Set up the Google Maps API client
gmaps = googlemaps.Client(key='AIzaSyBM79xqo29-jRQ4ThWv9yrXyTGBIZiMBvY')

# Set up the Google Cloud NL API client
client = language_v1.LanguageServiceClient()

# Set up the Streamlit user interface
st.set_page_config(
    page_title='Reviews Fetcher',
    page_icon=':mag:',
    layout='wide',
    initial_sidebar_state='expanded',
)

st.title('Reviews Fetcher')

# Set up the Glass Morphism style
st.markdown("""
    <style>
    .main {
        background: linear-gradient(to bottom right, #ffffff, #f1f1f1);
        padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0 1rem 2rem rgba(0, 0, 0, 0.2);
    }
    .chart {
        background: linear-gradient(to bottom right, #ffffff, #f1f1f1);
        padding: 2rem;
        border-radius: 1rem;
        box-shadow: 0 1rem 2rem rgba(0, 0, 0, 0.2);
        margin-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Set up the user input
location = st.text_input('Enter a location:', '')

if location:
    st.write(f'Reviews fetching for {location}...')

    # Use the Google Maps Places API to get the place ID for the location
    place = gmaps.find_place(
        input=location,
        input_type='textquery',
        fields=['place_id']
    )

    if place['status'] == 'OK':
        place_id = place['candidates'][0]['place_id']

        # Use the Google Maps Places API to get the place details and reviews
        place_details = gmaps.place(
            place_id=place_id,
            fields=['name', 'formatted_address', 'rating', 'reviews']
        )

        if place_details['status'] == 'OK':
            place_name = place_details['result']['name']
            place_address = place_details['result']['formatted_address']
            place_rating = place_details['result']['rating']
            place_reviews = place_details['result']['reviews']

            # Create a Pandas DataFrame to store the reviews
            reviews_df = pd.DataFrame(place_reviews)
            reviews_df['place_name'] = place_name
            reviews_df['place_address'] = place_address
            reviews_df['place_rating'] = place_rating

            # Set up the progress bar
            progress_bar = st.progress(0)
            progress_text = st.empty()

            # Process each review using the Google Cloud NL API and update the sentiment score in the DataFrame
            for i, review in reviews_df.iterrows():
                document = language_v1.Document(content=review['text'], type_=language_v1.Document.Type.PLAIN_TEXT)#error
                sentiment = client.analyze_sentiment(document=document).document_sentiment.score
                reviews_df.at[i, 'sentiment'] = sentiment

                # Update the progress bar
                progress_bar.progress((i + 1) / len(reviews_df))
                progress_text.text(f'Processing review {i + 1}/{len(reviews_df)}...')
                time.sleep(0.1)

            # Save the reviews to a CSV file
            reviews_df.to_csv(f'{place_name}_reviews.csv', index=False)

        # Display the reviews in a table
        st.write(reviews_df)

        # Create the time series chart
        chart_data = reviews_df[['time', 'sentiment']]
        chart_data['time'] = pd.to_datetime(chart_data['time'], unit='s')

        fig = px.line(chart_data, x='time', y='sentiment', title='Sentiment over Time')
        fig.update_layout(
            xaxis_title='Time',
            yaxis_title='Sentiment Score',
            template='plotly_white',
            font=dict(
                size=12
            ),
            margin=dict(
                l=50,
                r=50,
                b=50,
                t=50
            ),
            height=500
        )

        # Set up the Glass Morphism style for the chart
        fig.update_traces(line=dict(color='rgba(0, 0, 0, 0.8)', width=2))

        fig.update_layout(
            title={
                'font': {
                    'size': 24,
                    'color': 'rgba(0, 0, 0, 0.8)'
                },
                'x': 0.5,
                'y': 0.92
            },
            plot_bgcolor='rgba(255, 255, 255, 0)',
            paper_bgcolor='rgba(255, 255, 255, 0)',
            hovermode='x unified'
        )

        # Display the chart with sliders for date range and sentiment range
        st.markdown("""
            <style>
            .js-plotly-plot .plotly__slider {
                background-color: rgba(255, 255, 255, 0.8) !important;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown('## Sentiment over Time')
        st.plotly_chart(fig, use_container_width=True)

        date_range = st.slider('Select a date range:', min_value=chart_data['time'].min(), max_value=chart_data['time'].max(), value=(chart_data['time'].min(), chart_data['time'].max()))
        sentiment_range = st.slider('Select a sentiment range:', min_value=chart_data['sentiment'].min(), max_value=chart_data['sentiment'].max(), value=(chart_data['sentiment'].min(), chart_data['sentiment'].max()))

        filtered_data = chart_data[(chart_data['time'] >= date_range[0]) & (chart_data['time'] <= date_range[1]) & (chart_data['sentiment'] >= sentiment_range[0]) & (chart_data['sentiment'] <= sentiment_range[1])]

        filtered_fig = px.line(filtered_data, x='time', y='sentiment', title='Sentiment over Time')
        filtered_fig.update_layout(
            xaxis_title='Time',
            yaxis_title='Sentiment Score',
            template='plotly_white',
            font=dict(
                size=12
            ),
            margin=dict(
                l=50,
                r=50,
                b=50,
                t=50
            ),
            height=500
        )

        # Set up the Glass Morphism style for the chart
        filtered_fig.update_traces(line=dict(color='rgba(0, 0, 0, 0.8)', width=2))

        filtered_fig.update_layout(
            title={
                'font': {
                    'size': 24,
                    'color': 'rgba(0, 0, 0, 0.8)'
                },
                'x': 0.5,
                'y': 0.92
            },
            plot_bgcolor='rgba(255, 255, 255, 0)',
            paper_bgcolor='rgba(255, 255, 255, 0)',
            hovermode='x unified'
        )

        # Display the filtered chart
        st.plotly_chart(filtered_fig, use_container_width=True)

    else:
        st.error('No reviews found for this location.')
        
