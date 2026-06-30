import { useState, useRef, useEffect } from 'react'
import { Search, X } from 'lucide-react'
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

export default function CitySearch() {
  const { selectedCity, setSelectedCity } = useAppStore()
  const [searchTerm, setSearchTerm] = useState(selectedCity || '')
  const [isOpen, setIsOpen] = useState(false)
  const [filteredCities, setFilteredCities] = useState(cities)
  const inputRef = useRef(null)
  const dropdownRef = useRef(null)

  // Filter cities based on search term
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredCities(cities)
    } else {
      const filtered = cities.filter(city =>
        city.toLowerCase().includes(searchTerm.toLowerCase())
      )
      setFilteredCities(filtered)
    }
  }, [searchTerm])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target) &&
          inputRef.current && !inputRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelectCity = (city) => {
    setSelectedCity(city)
    setSearchTerm(city)
    setIsOpen(false)
  }

  const handleClear = () => {
    setSearchTerm('')
    setSelectedCity('Delhi')
    setIsOpen(false)
  }

  return (
    <div className="relative flex-1">
      <div className="relative">
        <Search className="absolute left-2 top-1/2 -translate-y-1/2 text-slate-500" size={14} />
        <input
          ref={inputRef}
          type="text"
          placeholder="Search city..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value)
            setIsOpen(true)
          }}
          onFocus={() => setIsOpen(true)}
          className="w-full bg-[#111827]/50 text-white text-sm rounded-lg pl-7 pr-8 py-1.5
                     border border-[#FF6B35]/30 focus:outline-none focus:border-[#FF6B35]
                     transition-colors placeholder:text-slate-500"
        />
        {searchTerm && (
          <button
            onClick={handleClear}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white"
          >
            <X size={14} />
          </button>
        )}
      </div>
      
      {/* Dropdown */}
      {isOpen && filteredCities.length > 0 && (
        <div
          ref={dropdownRef}
          className="absolute top-full left-0 right-0 mt-1 max-h-48 overflow-y-auto
                     bg-[#111827] border border-[#FF6B35]/30 rounded-lg shadow-lg z-50"
        >
          {filteredCities.map((city) => (
            <button
              key={city}
              onClick={() => handleSelectCity(city)}
              className={`w-full text-left px-3 py-1.5 text-sm transition-colors
                ${city === selectedCity
                  ? 'bg-[#FF6B35]/20 text-[#FF6B35]'
                  : 'text-white hover:bg-[#1a1a2e]'
                }`}
            >
              {city}
              {city === selectedCity && (
                <span className="float-right text-[#FF6B35] text-xs">✓</span>
              )}
            </button>
          ))}
        </div>
      )}
      
      {/* No results */}
      {isOpen && filteredCities.length === 0 && searchTerm.trim() !== '' && (
        <div className="absolute top-full left-0 right-0 mt-1 p-2
                       bg-[#111827] border border-[#FF6B35]/30 rounded-lg shadow-lg z-50">
          <p className="text-xs text-slate-500 text-center">No cities found</p>
        </div>
      )}
    </div>
  )
}