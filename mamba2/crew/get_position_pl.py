import pandas as pd
import os
from datetime import datetime

async def update_position_pl(csv_path, broker):
    """
    Update the CSV with position P/L and close time for closed positions.
    If the file doesn't exist, create it with the required columns.
    """
    try:
        # Check if file exists, if not create it with required columns
        if not os.path.exists(csv_path):
            df = pd.DataFrame(columns=['ticket', 'symbol', 'volume', 'open_price', 'open_time', 
                                     'sl', 'tp', 'pl', 'close_time', 'unfilled'])
            df['unfilled'] = False
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            df.to_csv(csv_path, index=False)
            return
            
        # File exists, proceed with normal processing
        df = pd.read_csv(csv_path)
        
        # If 'unfilled' column doesn't exist, create it and set all to False
        # since we don't know the status of these positions
        if 'unfilled' not in df.columns:
            df['unfilled'] = False
            df.to_csv(csv_path, index=False)
            return
            
        # Find rows that are still unfilled
        unfilled_rows = df[df['unfilled'] == True]
        for index, row in unfilled_rows.iterrows():
            ticket = row['ticket']
            position = await broker.position_by_ticket(ticket)
            if position is None:
                # Position not found, mark as filled to avoid future checks
                df.at[index, 'unfilled'] = False
                continue
            
            # Check if the position is closed (assuming the position object has a 'close_time')
            if hasattr(position, 'close_time') and position.close_time is not None:
                # Update the row with profit and close time
                df.at[index, 'pl'] = position.profit
                df.at[index, 'close_time'] = position.close_time
                df.at[index, 'unfilled'] = False
        
        # Save the updated DataFrame
        df.to_csv(csv_path, index=False)
        
    except Exception as e:
        print(f"Error updating position P/L: {e}")
        # Don't re-raise the exception to prevent task from failing
        return