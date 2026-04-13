import 'bootstrap/dist/css/bootstrap.min.css';
interface SelectProps {
  options: string[];
  defaultText: string;
  className?: string;
  disabled?: boolean;
  onChange: (value: string) => void;
}

export default function CustomSelect({
  options,
  defaultText,
  onChange,
  disabled = false,
}: SelectProps) {
  return (
    <select
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      defaultValue=""
    >
      <option value="" >
        {defaultText}
      </option>

      {options.map((opt) => (
        <option key={opt} value={opt}>
          {opt}
        </option>
      ))}
    </select>
  );
}