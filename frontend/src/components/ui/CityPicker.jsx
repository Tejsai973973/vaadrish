import useAppStore from '../../store/useAppStore'

const cities = [
  'Delhi', 'Mumbai', 'Bangalore', 'Chennai', 'Kolkata',
  'Hyderabad', 'Ahmedabad', 'Pune', 'Jaipur', 'Lucknow',
  'Kanpur', 'Patna', 'Varanasi', 'Agra', 'Noida',
  'Gurgaon', 'Faridabad', 'Ghaziabad', 'Amritsar', 'Ludhiana',
  'Chandigarh', 'Bhopal', 'Indore', 'Nagpur', 'Visakhapatnam',
  'Kochi', 'Coimbatore', 'Bhubaneswar', 'Guwahati', 'Dehradun',
  'Jodhpur', 'Raipur', 'Ranchi', 'Thiruvananthapuram', 'Mysuru',
  'Srinagar', 'Shimla', 'Meerut', 'Allahabad', 'Bareilly',
  'Aligarh', 'Moradabad', 'Gorakhpur', 'Jamshedpur', 'Dhanbad',
  'Bokaro', 'Kolhapur', 'Nashik'
]

export default function CityPicker() {
  const { selectedCity, setSelectedCity } = useAppStore()

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-slate-400 font-mono">City:</span>
      <select
        value={selectedCity}
        onChange={(e) => setSelectedCity(e.target.value)}
        className="bg-[#111827]/50 text-white text-sm rounded-lg px-3 py-1.5 
                   border border-[#FF6B35]/30 focus:outline-none 
                   focus:border-[#FF6B35] transition-colors cursor-pointer
                   hover:border-[#FF6B35]/60"
      >
        {cities.map(city => (
          <option key={city} value={city} className="bg-[#111827]">
            {city}
          </option>
        ))}
      </select>
    </div>
  )
}