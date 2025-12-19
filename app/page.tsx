"use client";

import React, { useState } from 'react';

// Types
interface Trip {
  date: string;
  trip_number: string;
  route: string;
  description: string;
  quantity: number;
  rate: number;
  amount: number;
}

interface Deduction {
  description: string;
  date: string;
  amount: number;
}

interface YTD {
  net: number;
  gross: number;
}

interface StatementData {
  recipient: {
    name: string;
    address_line_1: string;
    address_line_2: string;
  };
  statement_info: {
    date: string;
    truck_number: string;
  };
  trips: Trip[];
  deductions: Deduction[];
  ytd: YTD;
}

const initialData: StatementData = {
  recipient: {
    name: "FITRIGHT LOGISTICS LLC",
    address_line_1: "3374 FLAMBOROUGH DR",
    address_line_2: "Orlando, FL 32835"
  },
  statement_info: {
    date: new Date().toLocaleDateString('en-US'),
    truck_number: "196"
  },
  trips: [
    {
      date: "12/01/25",
      trip_number: "1743657425.00",
      route: "Salem, MA-Murfreesboro, TN",
      description: "30% of $2,000.00",
      quantity: 2000.00,
      rate: 0.3000,
      amount: 600.00
    }
  ],
  deductions: [
    {
      description: "OCCUPATIONAL ACCIDENTAL INSURANCE",
      date: "12/04/25",
      amount: -37.50
    }
  ],
  ytd: {
    net: 22801.41,
    gross: 28826.40
  }
};

export default function Home() {
  const [data, setData] = useState<StatementData>(initialData);
  const [loading, setLoading] = useState(false);

  const handleRecipientChange = (field: string, value: string) => {
    setData(prev => ({
      ...prev,
      recipient: { ...prev.recipient, [field]: value }
    }));
  };

  const handleInfoChange = (field: string, value: string) => {
    setData(prev => ({
      ...prev,
      statement_info: { ...prev.statement_info, [field]: value }
    }));
  };

  const handleYTDChange = (field: string, value: string) => {
    setData(prev => ({
      ...prev,
      ytd: { ...prev.ytd, [field]: parseFloat(value) || 0 }
    }));
  };

  // Trips Management
  const addTrip = () => {
    setData(prev => ({
      ...prev,
      trips: [...prev.trips, { date: "", trip_number: "", route: "", description: "", quantity: 0, rate: 0, amount: 0 }]
    }));
  };

  const updateTrip = (index: number, field: keyof Trip, value: string | number) => {
    const newTrips = [...data.trips];
    // @ts-expect-error - dynamic assignment
    newTrips[index][field] = value;
    setData(prev => ({ ...prev, trips: newTrips }));
  };

  const removeTrip = (index: number) => {
    setData(prev => ({
      ...prev,
      trips: prev.trips.filter((_, i) => i !== index)
    }));
  };

  // Deductions Management
  const addDeduction = () => {
    setData(prev => ({
      ...prev,
      deductions: [...prev.deductions, { description: "", date: "", amount: 0 }]
    }));
  };

  const updateDeduction = (index: number, field: keyof Deduction, value: string | number) => {
    const newDeductions = [...data.deductions];
    // @ts-expect-error - dynamic assignment
    newDeductions[index][field] = value;
    setData(prev => ({ ...prev, deductions: newDeductions }));
  };

  const removeDeduction = (index: number) => {
    setData(prev => ({
      ...prev,
      deductions: prev.deductions.filter((_, i) => i !== index)
    }));
  };

  const generatePDF = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/index.py', { // Vercel might route /api/index.py or just /api depending on config. Trying direct path first or /api/
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        // Fallback to /api if /api/index.py fails (local dev vs vercel)
         const response2 = await fetch('/api', { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
         });
         if(!response2.ok) throw new Error('Failed to generate PDF');
         const blob = await response2.blob();
         const url = window.URL.createObjectURL(blob);
         const a = document.createElement('a');
         a.href = url;
         a.download = `statement_${data.statement_info.truck_number}_${data.statement_info.date.replace(/\//g, '-')}.pdf`;
         document.body.appendChild(a);
         a.click();
         a.remove();
         return;
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `statement_${data.statement_info.truck_number}_${data.statement_info.date.replace(/\//g, '-')}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (error) {
      console.error(error);
      alert('Error generating PDF. Please check the console.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto">
        <div className="bg-white shadow-xl rounded-lg overflow-hidden">
          <div className="bg-blue-600 px-6 py-4">
            <h1 className="text-2xl font-bold text-white">Statement Generator</h1>
          </div>
          
          <div className="p-6 space-y-8">
            
            {/* Recipient & Statement Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900 border-b pb-2">Recipient Info</h3>
                <input type="text" placeholder="Name" className="w-full p-2 border rounded" value={data.recipient.name} onChange={e => handleRecipientChange('name', e.target.value)} />
                <input type="text" placeholder="Address Line 1" className="w-full p-2 border rounded" value={data.recipient.address_line_1} onChange={e => handleRecipientChange('address_line_1', e.target.value)} />
                <input type="text" placeholder="Address Line 2" className="w-full p-2 border rounded" value={data.recipient.address_line_2} onChange={e => handleRecipientChange('address_line_2', e.target.value)} />
              </div>
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900 border-b pb-2">Statement Info</h3>
                <div className="grid grid-cols-2 gap-4">
                  <input type="text" placeholder="Date" className="w-full p-2 border rounded" value={data.statement_info.date} onChange={e => handleInfoChange('date', e.target.value)} />
                  <input type="text" placeholder="Truck #" className="w-full p-2 border rounded" value={data.statement_info.truck_number} onChange={e => handleInfoChange('truck_number', e.target.value)} />
                </div>
                <h3 className="text-lg font-medium text-gray-900 border-b pb-2 pt-4">YTD Totals</h3>
                 <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-gray-500">Net YTD</label>
                    <input type="number" step="0.01" className="w-full p-2 border rounded" value={data.ytd.net} onChange={e => handleYTDChange('net', e.target.value)} />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500">Gross YTD</label>
                    <input type="number" step="0.01" className="w-full p-2 border rounded" value={data.ytd.gross} onChange={e => handleYTDChange('gross', e.target.value)} />
                  </div>
                </div>
              </div>
            </div>

            {/* Trips */}
            <div>
              <div className="flex justify-between items-center border-b pb-2 mb-4">
                <h3 className="text-lg font-medium text-gray-900">Trips</h3>
                <button onClick={addTrip} className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-sm">Add Trip</button>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Trip #</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Route</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Qty</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Rate</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                      <th className="px-3 py-2"></th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {data.trips.map((trip, idx) => (
                      <tr key={idx}>
                        <td className="p-2"><input className="w-full border rounded p-1 text-sm" value={trip.date} onChange={e => updateTrip(idx, 'date', e.target.value)} /></td>
                        <td className="p-2"><input className="w-full border rounded p-1 text-sm" value={trip.trip_number} onChange={e => updateTrip(idx, 'trip_number', e.target.value)} /></td>
                        <td className="p-2"><input className="w-full border rounded p-1 text-sm" value={trip.route} onChange={e => updateTrip(idx, 'route', e.target.value)} /></td>
                        <td className="p-2"><input className="w-full border rounded p-1 text-sm" value={trip.description} onChange={e => updateTrip(idx, 'description', e.target.value)} /></td>
                        <td className="p-2"><input type="number" step="0.01" className="w-20 border rounded p-1 text-sm" value={trip.quantity} onChange={e => updateTrip(idx, 'quantity', parseFloat(e.target.value))} /></td>
                        <td className="p-2"><input type="number" step="0.0001" className="w-20 border rounded p-1 text-sm" value={trip.rate} onChange={e => updateTrip(idx, 'rate', parseFloat(e.target.value))} /></td>
                        <td className="p-2"><input type="number" step="0.01" className="w-24 border rounded p-1 text-sm" value={trip.amount} onChange={e => updateTrip(idx, 'amount', parseFloat(e.target.value))} /></td>
                        <td className="p-2 text-center"><button onClick={() => removeTrip(idx)} className="text-red-600 hover:text-red-900">×</button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Deductions */}
            <div>
              <div className="flex justify-between items-center border-b pb-2 mb-4">
                <h3 className="text-lg font-medium text-gray-900">Deductions</h3>
                <button onClick={addDeduction} className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-sm">Add Deduction</button>
              </div>
               <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                      <th className="px-3 py-2"></th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {data.deductions.map((ded, idx) => (
                      <tr key={idx}>
                        <td className="p-2"><input className="w-full border rounded p-1 text-sm" value={ded.description} onChange={e => updateDeduction(idx, 'description', e.target.value)} /></td>
                        <td className="p-2"><input className="w-full border rounded p-1 text-sm" value={ded.date} onChange={e => updateDeduction(idx, 'date', e.target.value)} /></td>
                        <td className="p-2"><input type="number" step="0.01" className="w-32 border rounded p-1 text-sm" value={ded.amount} onChange={e => updateDeduction(idx, 'amount', parseFloat(e.target.value))} /></td>
                         <td className="p-2 text-center"><button onClick={() => removeDeduction(idx)} className="text-red-600 hover:text-red-900">×</button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Action */}
            <div className="pt-6 border-t flex justify-end">
              <button 
                onClick={generatePDF} 
                disabled={loading}
                className={`px-6 py-3 bg-blue-600 text-white font-medium rounded shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                {loading ? 'Generating...' : 'Generate PDF'}
              </button>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}
